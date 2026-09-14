#!/usr/bin/env python3
"""Direct/non-thinking generation-task evaluation against CETVEL's own tasks,
run through the CETVEL venv's local Transformers backend instead of vLLM.

Fallback for evaluate_cetvel_generation_vllm.py: the vLLM nightly available
at run time hard-requires a CUDA 13-capable driver (see
docs/environment-setup-gotchas.md, "vLLM nightly requiring newer CUDA driver
than the pod has"), which this pod's driver does not meet. Transformers
5.17.0 already recognizes Qwen3.5 natively (Qwen3_5ForConditionalGeneration),
so this backend swap changes only inference speed, not correctness -- the
frozen protocol already specifies concurrency=1, so there is no batching
difference either.

Task configs (dataset paths, prompt templates, stop strings, output caps) are
copied verbatim from evaluate_cetvel_generation_vllm.py. Metrics are NOT
computed here; see score_cetvel_generation.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import datasets
import torch
from datasets import load_dataset
from huggingface_hub import HfApi
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "Qwen/Qwen3.5-4B"
MODEL_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def git_output(command: list[str], cwd: Path) -> str | None:
    try:
        return subprocess.check_output(command, cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


# --- Per-task config: dataset source, prompt template, stop strings -------
# Copied verbatim from evaluate_cetvel_generation_vllm.py.

def _gecturk_prompt(doc: dict) -> str:
    return f"Verilen cumlenin yazım hatalarını duzeltin.\nHatalı Cümle: {doc['source']}\nDüzeltilmiş hali: "


def _gecturk_target(doc: dict) -> str:
    return doc["target"]


def _tquad_prompt(doc: dict) -> str:
    return f"Kaynak: {doc['context']}\n\nSoru: {doc['question']}\n\nCevap:"


def _squad_style_target(doc: dict) -> dict:
    return {"id": doc["id"], "answers": doc["answers"]}


def _xquad_prompt(doc: dict) -> str:
    return f"Kaynak: {doc['context']}\n\nSoru: {doc['question']}\n\nCevap:"


def _wmt_en_tr_prompt(doc: dict) -> str:
    return f"Translate English to Turkish.\n\nEnglish: {doc['translation']['en']}\nTurkish:"


def _wmt_en_tr_target(doc: dict) -> str:
    return doc["translation"]["tr"]


def _mlsum_prompt(doc: dict) -> str:
    return f"Başlık: {doc['title']}\n\nMetin: {doc['text']}\n\nÖzet:"


def _mlsum_target(doc: dict) -> str:
    return doc["summary"]


TASKS = {
    "gecturk": {
        "dataset_path": "mcemilg/GECTurk-generation", "dataset_name": None, "split": "test",
        "prompt_fn": _gecturk_prompt, "target_fn": _gecturk_target, "stop": ["\n"], "default_max_tokens": 128,
    },
    "tquad": {
        "dataset_path": "mcemilg/tquad", "dataset_name": None, "split": "validation",
        "prompt_fn": _tquad_prompt, "target_fn": _squad_style_target, "stop": ["\n"], "default_max_tokens": 128,
    },
    "xquad_tr": {
        "dataset_path": "google/xquad", "dataset_name": "xquad.tr", "split": "validation",
        "prompt_fn": _xquad_prompt, "target_fn": _squad_style_target, "stop": ["\n"], "default_max_tokens": 128,
    },
    "wmt_en_tr": {
        "dataset_path": "wmt/wmt16", "dataset_name": "tr-en", "split": "validation",
        "prompt_fn": _wmt_en_tr_prompt, "target_fn": _wmt_en_tr_target, "stop": None, "default_max_tokens": 256,
    },
    "mlsum_tr": {
        "dataset_path": "reciTAL/mlsum", "dataset_name": "tu", "split": "test",
        "prompt_fn": _mlsum_prompt, "target_fn": _mlsum_target, "stop": None, "default_max_tokens": 768,
    },
}


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, choices=sorted(TASKS))
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--max-new-tokens", type=int, default=None)
    parser.add_argument("--seed", type=int, default=3407)
    return parser.parse_args()


def main() -> int:
    cfg = args()
    cfg.output_dir.mkdir(parents=True, exist_ok=False)
    task_cfg = TASKS[cfg.task]
    max_new_tokens = cfg.max_new_tokens or task_cfg["default_max_tokens"]
    repo = Path(__file__).resolve().parents[2]

    torch.manual_seed(cfg.seed)

    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=MODEL_REVISION)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, revision=MODEL_REVISION, dtype=torch.bfloat16, device_map="cuda",
    )
    model.eval()

    try:
        resolved_revision = HfApi().dataset_info(task_cfg["dataset_path"]).sha
    except Exception:
        resolved_revision = None
    data = load_dataset(
        task_cfg["dataset_path"], task_cfg["dataset_name"], split=task_cfg["split"], trust_remote_code=True,
    )
    end_index = cfg.start_index + cfg.limit
    if cfg.start_index < 0 or cfg.limit < 1 or end_index > len(data):
        raise ValueError(f"range [{cfg.start_index}, {end_index}) out of bounds for dataset of size {len(data)}")
    selected = data.select(range(cfg.start_index, end_index))

    documents_blob = "\n".join(canonical(doc) for doc in selected)
    diff = git_output(["git", "diff", "--binary", "HEAD"], repo)
    manifest = {
        "protocol": "cetvel-generation-direct-transformers-v1",
        "fallback_reason": "vllm nightly at run time required a CUDA-13-capable driver this pod's driver (570.195.03, max CUDA 12.8) does not meet -- see docs/environment-setup-gotchas.md",
        "task": cfg.task,
        "model": {"name": MODEL, "revision": MODEL_REVISION, "dtype": "bfloat16"},
        "backend": {"engine": "transformers", "mode": "direct", "enable_thinking": False},
        "dataset": {
            "name": task_cfg["dataset_path"], "config": task_cfg["dataset_name"], "split": task_cfg["split"],
            "resolved_revision": resolved_revision,
            "selection": f"range({cfg.start_index},{end_index})", "selected_documents_sha256": digest(documents_blob),
        },
        "decoding": {
            "do_sample": False, "temperature": 0.0, "max_new_tokens": max_new_tokens,
            "stop": task_cfg["stop"], "concurrency": 1,
        },
        "reproducibility": {"seed": cfg.seed, "python_hash_seed": os.environ.get("PYTHONHASHSEED")},
        "software": {
            "python": sys.version, "platform": platform.platform(), "datasets": datasets.__version__,
            "torch": torch.__version__,
        },
        "repository": {"commit": git_output(["git", "rev-parse", "HEAD"], repo), "dirty_diff_sha256": digest(diff) if diff is not None else None},
        "started_at_unix": time.time(),
    }
    (cfg.output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    totals = {"truncated": 0, "prompt_tokens": 0, "generated_tokens": 0, "generation_seconds": 0.0}
    rows: list[dict] = []
    for index, doc in enumerate(selected, start=cfg.start_index):
        prompt = task_cfg["prompt_fn"](doc)
        target = task_cfg["target_fn"](doc)
        messages = [{"role": "user", "content": prompt}]
        encoded = tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True, enable_thinking=False,
            return_tensors="pt", return_dict=True,
        ).to(model.device)
        input_ids = encoded["input_ids"]
        prompt_len = input_ids.shape[1]

        started = time.perf_counter()
        generate_kwargs = dict(
            input_ids=input_ids,
            attention_mask=encoded.get("attention_mask"),
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None,
            top_p=None,
            top_k=None,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
        )
        if task_cfg["stop"]:
            generate_kwargs["stop_strings"] = task_cfg["stop"]
            generate_kwargs["tokenizer"] = tokenizer
        with torch.no_grad():
            output_ids = model.generate(**generate_kwargs)
        latency = time.perf_counter() - started

        new_tokens = output_ids[0, prompt_len:]
        content = tokenizer.decode(new_tokens, skip_special_tokens=True)
        # Strip a trailing stop string manually -- generate()'s stop_strings
        # keeps the match in the output, unlike vLLM's `stop` which cuts it.
        if task_cfg["stop"]:
            for s in task_cfg["stop"]:
                if content.endswith(s):
                    content = content[: -len(s)]
                    break
        generated_len = int(new_tokens.shape[0])
        hit_cap = generated_len >= max_new_tokens
        finish_reason = "length" if hit_cap else "stop"

        row = {
            "index": index, "document_sha256": digest(canonical(doc)),
            "document": doc, "semantic_prompt": prompt, "target": target,
            "raw_output": content, "reasoning": "",
            "finish_reason": finish_reason,
            "prompt_tokens": int(prompt_len), "generated_tokens": generated_len,
            "hit_max_new_tokens": hit_cap, "latency_seconds": latency,
        }
        rows.append(row)
        totals["truncated"] += int(hit_cap)
        totals["prompt_tokens"] += row["prompt_tokens"]; totals["generated_tokens"] += row["generated_tokens"]
        totals["generation_seconds"] += latency
        print(canonical({"index": index, "generated_tokens": row["generated_tokens"], "truncated": hit_cap, "latency_seconds": round(latency, 3), "progress": f"{len(rows)}/{cfg.limit}"}), flush=True)

    rows.sort(key=lambda r: r["index"])
    sample_path = cfg.output_dir / "samples.jsonl"
    with sample_path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    summary = {
        "protocol": manifest["protocol"], "task": cfg.task, "items": cfg.limit, **totals,
        "truncation_rate": totals["truncated"] / cfg.limit,
        "mean_generated_tokens": totals["generated_tokens"] / cfg.limit,
        "mean_latency_seconds": totals["generation_seconds"] / cfg.limit,
        "wall_seconds": time.time() - manifest["started_at_unix"],
        "samples_sha256": digest(sample_path.read_text(encoding="utf-8")),
    }
    (cfg.output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
