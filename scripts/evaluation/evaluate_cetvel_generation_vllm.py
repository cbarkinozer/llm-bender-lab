#!/usr/bin/env python3
"""Direct/non-thinking generation-task evaluation against CETVEL's own tasks,
run through vLLM instead of CETVEL's slower Transformers-backed harness.

Prompt templates, dataset paths, and stop strings are copied verbatim from
the pinned CETVEL task configs (see protocol-notes.md for the exact source
file per task) so results are comparable to what CETVEL itself would score,
modulo the faster backend. Metrics are NOT computed here -- this script only
generates and retains raw output; see score_cetvel_generation.py for
task-native scoring (SQuAD EM/F1, BLEU/chrF, ROUGE, GEC exact-match +
format-failure heuristics), which runs in the CETVEL venv where those metric
libraries are already installed.

Frozen for this round: temperature=0, do_sample=false, native chat template
with enable_thinking=false (direct mode only), per-task stop strings taken
from CETVEL's own generation_kwargs/until. Every item's full prompt and raw
output is retained regardless of correctness.
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
from datasets import load_dataset
from huggingface_hub import HfApi
from openai import OpenAI

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
# All copied verbatim from the pinned CETVEL task configs.

def _gecturk_prompt(doc: dict) -> str:
    return f"Verilen cumlenin yazım hatalarını duzeltin.\nHatalı Cümle: {doc['source']}\nDüzeltilmiş hali: "


def _gecturk_target(doc: dict) -> str:
    return doc["target"]


def _tquad_prompt(doc: dict) -> str:
    return f"Kaynak: {doc['context']}\n\nSoru: {doc['question']}\n\nCevap:"


def _squad_style_target(doc: dict) -> dict:
    # Keep the full answer set (not just the first) for SQuAD-style scoring.
    return {"id": doc["id"], "answers": doc["answers"]}


def _xquad_prompt(doc: dict) -> str:
    return f"Kaynak: {doc['context']}\n\nSoru: {doc['question']}\n\nCevap:"


def _wmt_en_tr_prompt(doc: dict) -> str:
    # CETVEL's own task is misleadingly named "wmt-tr-en-prompt" but its
    # actual prompt is English source -> Turkish target -- see
    # protocol-notes.md. This is intentionally the EN->TR direction: a
    # direct test of Turkish generation quality, not TR comprehension.
    return f"Translate English to Turkish.\n\nEnglish: {doc['translation']['en']}\nTurkish:"


def _wmt_en_tr_target(doc: dict) -> str:
    return doc["translation"]["tr"]


def _mlsum_prompt(doc: dict) -> str:
    return f"Başlık: {doc['title']}\n\nMetin: {doc['text']}\n\nÖzet:"


def _mlsum_target(doc: dict) -> str:
    return doc["summary"]


TASKS = {
    "gecturk": {
        "dataset_path": "mcemilg/GECTurk-generation",
        "dataset_name": None,
        "split": "test",
        "prompt_fn": _gecturk_prompt,
        "target_fn": _gecturk_target,
        "stop": ["\n"],
        "default_max_tokens": 128,
    },
    "tquad": {
        "dataset_path": "mcemilg/tquad",
        "dataset_name": None,
        "split": "validation",
        "prompt_fn": _tquad_prompt,
        "target_fn": _squad_style_target,
        "stop": ["\n"],
        "default_max_tokens": 128,
    },
    "xquad_tr": {
        "dataset_path": "google/xquad",
        "dataset_name": "xquad.tr",
        "split": "validation",
        "prompt_fn": _xquad_prompt,
        "target_fn": _squad_style_target,
        "stop": ["\n"],
        "default_max_tokens": 128,
    },
    "wmt_en_tr": {
        "dataset_path": "wmt/wmt16",
        "dataset_name": "tr-en",
        "split": "validation",
        "prompt_fn": _wmt_en_tr_prompt,
        "target_fn": _wmt_en_tr_target,
        "stop": None,
        "default_max_tokens": 256,
    },
    "mlsum_tr": {
        "dataset_path": "reciTAL/mlsum",
        "dataset_name": "tu",
        "split": "test",
        "prompt_fn": _mlsum_prompt,
        "target_fn": _mlsum_target,
        "stop": None,
        "default_max_tokens": 768,
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
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def main() -> int:
    cfg = args()
    cfg.output_dir.mkdir(parents=True, exist_ok=False)
    task_cfg = TASKS[cfg.task]
    max_new_tokens = cfg.max_new_tokens or task_cfg["default_max_tokens"]
    repo = Path(__file__).resolve().parents[2]

    try:
        resolved_revision = HfApi().dataset_info(task_cfg["dataset_path"]).sha
    except Exception:
        resolved_revision = None
    data = load_dataset(task_cfg["dataset_path"], task_cfg["dataset_name"], split=task_cfg["split"])
    end_index = cfg.start_index + cfg.limit
    if cfg.start_index < 0 or cfg.limit < 1 or end_index > len(data):
        raise ValueError(f"range [{cfg.start_index}, {end_index}) out of bounds for dataset of size {len(data)}")
    selected = data.select(range(cfg.start_index, end_index))
    client = OpenAI(base_url=f"http://127.0.0.1:{cfg.port}/v1", api_key="EMPTY")

    documents_blob = "\n".join(canonical(doc) for doc in selected)
    diff = git_output(["git", "diff", "--binary", "HEAD"], repo)
    manifest = {
        "protocol": "cetvel-generation-direct-vllm-v1",
        "task": cfg.task,
        "model": {"name": MODEL, "revision": MODEL_REVISION, "dtype": "bfloat16"},
        "backend": {"engine": "vllm", "mode": "direct", "enable_thinking": False},
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
        "software": {"python": sys.version, "platform": platform.platform(), "datasets": datasets.__version__},
        "repository": {"commit": git_output(["git", "rev-parse", "HEAD"], repo), "dirty_diff_sha256": digest(diff) if diff is not None else None},
        "started_at_unix": time.time(),
    }
    (cfg.output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    totals = {"truncated": 0, "prompt_tokens": 0, "generated_tokens": 0, "generation_seconds": 0.0}
    rows: list[dict] = []
    for index, doc in enumerate(selected, start=cfg.start_index):
        prompt = task_cfg["prompt_fn"](doc)
        target = task_cfg["target_fn"](doc)
        started = time.perf_counter()
        extra_body = {"chat_template_kwargs": {"enable_thinking": False}}
        request_kwargs = dict(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=max_new_tokens,
            extra_body=extra_body,
        )
        if task_cfg["stop"]:
            request_kwargs["stop"] = task_cfg["stop"]
        response = client.chat.completions.create(**request_kwargs)
        latency = time.perf_counter() - started
        message = response.choices[0].message
        content = message.content or ""
        reasoning = getattr(message, "reasoning", None) or ""
        usage = response.usage
        hit_cap = response.choices[0].finish_reason == "length"
        row = {
            "index": index, "document_sha256": digest(canonical(doc)),
            "document": doc, "semantic_prompt": prompt, "target": target,
            "raw_output": content, "reasoning": reasoning,
            "finish_reason": response.choices[0].finish_reason,
            "prompt_tokens": usage.prompt_tokens, "generated_tokens": usage.completion_tokens,
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
