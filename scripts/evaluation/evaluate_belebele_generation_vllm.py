#!/usr/bin/env python3
"""Deterministic generated-answer evaluation for Turkish Belebele, vLLM backend.

Mirrors evaluate_belebele_generation.py (Transformers backend) field-for-field
so the two protocols are directly comparable, but issues requests to a running
vLLM OpenAI-compatible server instead of calling model.generate() locally.
Requests are sent sequentially (one in flight at a time) to match the
Transformers protocol's batch_size=1 and keep this run free of concurrent-
batching nondeterminism; see docs/evaluation-guide.md before enabling
concurrency here.

Do not compare scores from this protocol against the CETVEL likelihood
baseline (belebele-dev) or mix them with the Transformers generation
calibration runs without noting the backend difference explicitly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

import datasets
from datasets import load_dataset
from openai import OpenAI

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
    parser.add_argument("--port", type=int, default=8000)
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


def make_prompt(doc: dict) -> str:
    return (
        "Aşağıdaki Türkçe metni okuyun ve soruyu yanıtlayın. Dört seçenekten yalnızca "
        "birini seçin. Yanıtınızın en sonunda tam olarak FINAL: X yazın; X yalnızca "
        "A, B, C veya D olabilir.\n\n"
        f"Metin:\n{doc['flores_passage']}\n\nSoru: {doc['question']}\n"
        f"A: {doc['mc_answer1']}\nB: {doc['mc_answer2']}\n"
        f"C: {doc['mc_answer3']}\nD: {doc['mc_answer4']}"
    )


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
    repo = Path(__file__).resolve().parents[2]
    data = load_dataset(DATASET, DATASET_CONFIG, split="test", revision=DATASET_REVISION)
    if not 1 <= cfg.limit <= len(data):
        raise ValueError(f"limit must be in [1, {len(data)}]")
    selected = data.select(range(cfg.limit))
    client = OpenAI(base_url=f"http://127.0.0.1:{cfg.port}/v1", api_key="EMPTY")

    documents_blob = "\n".join(canonical(doc) for doc in selected)
    prompts_blob = "\n".join(make_prompt(doc) for doc in selected)
    diff = git_output(["git", "diff", "--binary", "HEAD"], repo)
    manifest = {
        "protocol": "belebele-turkish-paired-generation-vllm-v1",
        "mode": cfg.mode,
        "model": {"name": MODEL, "revision": MODEL_REVISION, "dtype": "bfloat16"},
        "backend": {
            "engine": "vllm", "reasoning_parser": "qwen3", "language_model_only": True,
            "flashinfer_sampler_disabled": os.environ.get("VLLM_USE_FLASHINFER_SAMPLER") == "0",
            "note": "reasoning/content already split server-side by --reasoning-parser qwen3; unlike the Transformers protocol, no local <think> tag parsing is needed",
        },
        "dataset": {"name": DATASET, "revision": DATASET_REVISION, "config": DATASET_CONFIG, "split": "test", "selection": f"range(0,{cfg.limit})", "selected_documents_sha256": digest(documents_blob)},
        "decoding": {"do_sample": False, "temperature": 0.0, "top_p": None, "top_k": None, "max_new_tokens": cfg.max_new_tokens, "concurrency": 1},
        "chat_template": {"native": True, "enable_thinking": cfg.mode == "thinking", "add_generation_prompt": True, "semantic_prompts_sha256": digest(prompts_blob)},
        "reproducibility": {"seed": cfg.seed, "python_hash_seed": os.environ.get("PYTHONHASHSEED")},
        "software": {"python": sys.version, "platform": platform.platform(), "datasets": datasets.__version__},
        "repository": {"commit": git_output(["git", "rev-parse", "HEAD"], repo), "dirty_diff_sha256": digest(diff) if diff is not None else None},
        "scoring": {"gold": "correct_answer_num mapped 1=A through 4=D", "parser": "last strict FINAL: [ABCD], then unique-letter fallback"},
        "started_at_unix": time.time(),
    }
    (cfg.output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    totals = {"correct": 0, "parsed": 0, "truncated": 0, "prompt_tokens": 0, "generated_tokens": 0, "reasoning_tokens": 0, "generation_seconds": 0.0}
    sample_path = cfg.output_dir / "samples.jsonl"
    with sample_path.open("w", encoding="utf-8", buffering=1) as stream:
        for index, doc in enumerate(selected):
            prompt = make_prompt(doc)
            started = time.perf_counter()
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=cfg.max_new_tokens,
                extra_body={"chat_template_kwargs": {"enable_thinking": cfg.mode == "thinking"}},
            )
            latency = time.perf_counter() - started
            message = response.choices[0].message
            content = message.content or ""
            reasoning = getattr(message, "reasoning", None) or ""
            raw = (reasoning + "\n" + content) if reasoning else content
            prediction, parser = extract_answer(content, raw)
            gold = LETTERS[int(doc["correct_answer_num"]) - 1]
            usage = response.usage
            hit_cap = response.choices[0].finish_reason == "length"
            reasoning_tokens = usage.completion_tokens_details.reasoning_tokens if usage.completion_tokens_details else None
            row = {
                "index": index, "document_sha256": digest(canonical(doc)), "semantic_prompt_sha256": digest(prompt),
                "document": doc, "semantic_prompt": prompt, "raw_output": raw, "reasoning": reasoning, "answer_text": content,
                "reasoning_language": language_heuristic(reasoning), "prediction": prediction, "gold": gold, "correct": prediction == gold, "parser": parser,
                "finish_reason": response.choices[0].finish_reason,
                "prompt_tokens": usage.prompt_tokens, "generated_tokens": usage.completion_tokens, "reasoning_tokens": reasoning_tokens,
                "hit_max_new_tokens": hit_cap, "latency_seconds": latency,
            }
            stream.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
            totals["correct"] += int(row["correct"]); totals["parsed"] += int(prediction is not None); totals["truncated"] += int(hit_cap)
            totals["prompt_tokens"] += row["prompt_tokens"]; totals["generated_tokens"] += row["generated_tokens"]
            totals["reasoning_tokens"] += reasoning_tokens or 0; totals["generation_seconds"] += latency
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
