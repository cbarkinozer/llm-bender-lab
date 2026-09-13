#!/usr/bin/env python3
"""Deterministic generated-answer evaluation for Turkish Belebele."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import re
import subprocess
import sys
import time
from pathlib import Path

import datasets
import numpy as np
import torch
import transformers
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "Qwen/Qwen3.5-4B"
MODEL_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
DATASET = "facebook/belebele"
DATASET_REVISION = "7899cdfa4e1e0d733fd77c848e2c273cb1d32be2"
DATASET_CONFIG = "tur_Latn"
LETTERS = "ABCD"
FINAL_RE = re.compile(r"(?im)^\s*(?:FINAL|NİHAİ\s+CEVAP|CEVAP)\s*:\s*([ABCD])\b")
LOOSE_RE = re.compile(r"(?i)\b([ABCD])\b")
TR_WORDS = {"ve", "bir", "bu", "için", "ile", "olarak", "cevap", "çünkü", "de", "da"}
EN_WORDS = {"the", "and", "this", "because", "answer", "is", "of", "to", "in", "that"}


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=("direct", "thinking"))
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--seed", type=int, default=3407)
    return parser.parse_args()


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def git_output(command: list[str], cwd: Path) -> str | None:
    try:
        return subprocess.check_output(command, cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def set_reproducibility(seed: int) -> None:
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def make_prompt(doc: dict) -> str:
    return (
        "Aşağıdaki Türkçe metni okuyun ve soruyu yanıtlayın. Dört seçenekten yalnızca "
        "birini seçin. Yanıtınızın en sonunda tam olarak FINAL: X yazın; X yalnızca "
        "A, B, C veya D olabilir.\n\n"
        f"Metin:\n{doc['flores_passage']}\n\nSoru: {doc['question']}\n"
        f"A: {doc['mc_answer1']}\nB: {doc['mc_answer2']}\n"
        f"C: {doc['mc_answer3']}\nD: {doc['mc_answer4']}"
    )


def split_output(raw: str) -> tuple[str, str]:
    if "</think>" not in raw:
        return "", raw.strip()
    reasoning, answer = raw.split("</think>", 1)
    return reasoning.removeprefix("<think>").strip(), answer.strip()


def extract_answer(answer: str, raw: str) -> tuple[str | None, str]:
    matches = FINAL_RE.findall(answer)
    if matches:
        return matches[-1].upper(), "strict_final"
    matches = FINAL_RE.findall(raw)
    if matches:
        return matches[-1].upper(), "strict_final_raw"
    loose = LOOSE_RE.findall(answer.strip())
    if len(loose) == 1:
        return loose[0].upper(), "single_letter_fallback"
    return None, "failed"


def language_heuristic(text: str) -> dict:
    words = re.findall(r"[^\W\d_]+", text.casefold(), flags=re.UNICODE)
    tr_score = sum(w in TR_WORDS for w in words) + sum(c in text.casefold() for c in "çğıöşü")
    en_score = sum(w in EN_WORDS for w in words)
    label = "unknown" if not text or max(tr_score, en_score) < 2 else ("turkish" if tr_score > en_score else "english" if en_score > tr_score else "mixed")
    return {"label": label, "turkish_score": tr_score, "english_score": en_score, "method": "stopword_character_heuristic_v1"}


def main() -> int:
    cfg = args()
    cfg.output_dir.mkdir(parents=True, exist_ok=False)
    set_reproducibility(cfg.seed)
    repo = Path(__file__).resolve().parents[2]
    data = load_dataset(DATASET, DATASET_CONFIG, split="test", revision=DATASET_REVISION)
    if not 1 <= cfg.limit <= len(data):
        raise ValueError(f"limit must be in [1, {len(data)}]")
    selected = data.select(range(cfg.limit))

    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=MODEL_REVISION)
    model = AutoModelForCausalLM.from_pretrained(MODEL, revision=MODEL_REVISION, dtype=torch.bfloat16, device_map="cuda:0")
    model.eval()

    documents_blob = "\n".join(canonical(doc) for doc in selected)
    prompts_blob = "\n".join(make_prompt(doc) for doc in selected)
    diff = git_output(["git", "diff", "--binary", "HEAD"], repo)
    manifest = {
        "protocol": "belebele-turkish-paired-generation-v1",
        "mode": cfg.mode,
        "model": {"name": MODEL, "revision": MODEL_REVISION, "dtype": "bfloat16"},
        "dataset": {"name": DATASET, "revision": DATASET_REVISION, "config": DATASET_CONFIG, "split": "test", "selection": f"range(0,{cfg.limit})", "selected_documents_sha256": digest(documents_blob)},
        "decoding": {"do_sample": False, "temperature": 0.0, "top_p": None, "top_k": None, "max_new_tokens": cfg.max_new_tokens, "batch_size": 1},
        "chat_template": {"native": True, "enable_thinking": cfg.mode == "thinking", "add_generation_prompt": True, "semantic_prompts_sha256": digest(prompts_blob)},
        "reproducibility": {"seed": cfg.seed, "python_hash_seed": os.environ.get("PYTHONHASHSEED"), "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG"), "cudnn_benchmark": torch.backends.cudnn.benchmark, "cudnn_deterministic": torch.backends.cudnn.deterministic},
        "software": {"python": sys.version, "platform": platform.platform(), "torch": torch.__version__, "transformers": transformers.__version__, "datasets": datasets.__version__},
        "hardware": {"gpu": torch.cuda.get_device_name(0), "cuda_runtime": torch.version.cuda, "bf16_supported": torch.cuda.is_bf16_supported()},
        "repository": {"commit": git_output(["git", "rev-parse", "HEAD"], repo), "dirty_diff_sha256": digest(diff) if diff is not None else None},
        "scoring": {"gold": "correct_answer_num mapped 1=A through 4=D", "parser": "last strict FINAL: [ABCD], then unique-letter fallback"},
        "started_at_unix": time.time(),
    }
    (cfg.output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    totals = {"correct": 0, "parsed": 0, "truncated": 0, "prompt_tokens": 0, "generated_tokens": 0, "generation_seconds": 0.0}
    sample_path = cfg.output_dir / "samples.jsonl"
    with sample_path.open("w", encoding="utf-8", buffering=1) as stream:
        for index, doc in enumerate(selected):
            prompt = make_prompt(doc)
            rendered = tokenizer.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True, enable_thinking=cfg.mode == "thinking")
            inputs = tokenizer(rendered, return_tensors="pt", add_special_tokens=False).to("cuda:0")
            torch.cuda.synchronize()
            started = time.perf_counter()
            with torch.inference_mode():
                output = model.generate(**inputs, do_sample=False, max_new_tokens=cfg.max_new_tokens, pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id, use_cache=True)
            torch.cuda.synchronize()
            latency = time.perf_counter() - started
            new_ids = output[0, inputs.input_ids.shape[1]:]
            raw = tokenizer.decode(new_ids, skip_special_tokens=True)
            reasoning, answer_text = split_output(raw)
            prediction, parser = extract_answer(answer_text, raw)
            gold = LETTERS[int(doc["correct_answer_num"]) - 1]
            row = {
                "index": index, "document_sha256": digest(canonical(doc)), "semantic_prompt_sha256": digest(prompt), "rendered_prompt_sha256": digest(rendered),
                "document": doc, "semantic_prompt": prompt, "rendered_prompt": rendered, "raw_output": raw, "reasoning": reasoning, "answer_text": answer_text,
                "reasoning_language": language_heuristic(reasoning), "prediction": prediction, "gold": gold, "correct": prediction == gold, "parser": parser,
                "prompt_tokens": int(inputs.input_ids.shape[1]), "generated_tokens": int(len(new_ids)), "hit_max_new_tokens": len(new_ids) >= cfg.max_new_tokens, "latency_seconds": latency,
            }
            stream.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
            totals["correct"] += int(row["correct"]); totals["parsed"] += int(prediction is not None); totals["truncated"] += int(row["hit_max_new_tokens"])
            totals["prompt_tokens"] += row["prompt_tokens"]; totals["generated_tokens"] += row["generated_tokens"]; totals["generation_seconds"] += latency
            print(canonical({"index": index, "prediction": prediction, "gold": gold, "correct": row["correct"], "generated_tokens": row["generated_tokens"], "latency_seconds": round(latency, 3)}), flush=True)

    summary = {
        "protocol": manifest["protocol"], "mode": cfg.mode, "items": cfg.limit, **totals,
        "accuracy": totals["correct"] / cfg.limit, "parser_success_rate": totals["parsed"] / cfg.limit,
        "max_new_tokens_hit_rate": totals["truncated"] / cfg.limit, "mean_generated_tokens": totals["generated_tokens"] / cfg.limit,
        "mean_latency_seconds": totals["generation_seconds"] / cfg.limit, "wall_seconds": time.time() - manifest["started_at_unix"],
        "samples_sha256": digest(sample_path.read_text(encoding="utf-8")),
    }
    (cfg.output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
