#!/usr/bin/env python3
"""One-item direct/thinking parity check for the vLLM Qwen3.5-4B backend.

Compares against the Transformers reference protocol in
evaluate_belebele_generation.py: same dataset revision, same semantic prompt,
same FINAL: X parser. Not a scored benchmark run -- a backend sanity check
before the 100-item paired evaluation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

from datasets import load_dataset
from openai import OpenAI

MODEL = "Qwen/Qwen3.5-4B"
DATASET = "facebook/belebele"
DATASET_REVISION = "7899cdfa4e1e0d733fd77c848e2c273cb1d32be2"
DATASET_CONFIG = "tur_Latn"
LETTERS = "ABCD"
FINAL_RE = re.compile(r"(?im)^\s*(?:FINAL|NİHAİ\s+CEVAP|CEVAP)\s*:\s*([ABCD])\b")
LOOSE_RE = re.compile(r"(?i)\b([ABCD])\b")


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


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def run_one(client: OpenAI, prompt: str, enable_thinking: bool, max_tokens: int) -> dict:
    started = time.perf_counter()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=max_tokens,
        extra_body={"chat_template_kwargs": {"enable_thinking": enable_thinking}},
    )
    latency = time.perf_counter() - started
    message = response.choices[0].message
    content = message.content or ""
    reasoning = getattr(message, "reasoning", None) or ""
    raw = reasoning + "\n" + content
    prediction, parser = extract_answer(content, raw)
    usage = response.usage
    return {
        "mode": "thinking" if enable_thinking else "direct",
        "finish_reason": response.choices[0].finish_reason,
        "reasoning": reasoning,
        "content": content,
        "prediction": prediction,
        "parser": parser,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "reasoning_tokens": (usage.completion_tokens_details.reasoning_tokens if usage.completion_tokens_details else None),
        "hit_max_tokens": response.choices[0].finish_reason == "length",
        "latency_seconds": latency,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--max-tokens-direct", type=int, default=512)
    parser.add_argument("--max-tokens-thinking", type=int, default=2048)
    cfg = parser.parse_args()
    cfg.output_dir.mkdir(parents=True, exist_ok=False)

    data = load_dataset(DATASET, DATASET_CONFIG, split="test", revision=DATASET_REVISION)
    doc = data[cfg.index]
    prompt = make_prompt(doc)
    gold = LETTERS[int(doc["correct_answer_num"]) - 1]

    client = OpenAI(base_url=f"http://127.0.0.1:{cfg.port}/v1", api_key="EMPTY")
    results = {
        "protocol": "belebele-turkish-vllm-parity-check-v1",
        "model": MODEL,
        "dataset": {"name": DATASET, "revision": DATASET_REVISION, "config": DATASET_CONFIG, "index": cfg.index},
        "semantic_prompt_sha256": digest(prompt),
        "gold": gold,
        "direct": run_one(client, prompt, enable_thinking=False, max_tokens=cfg.max_tokens_direct),
        "thinking": run_one(client, prompt, enable_thinking=True, max_tokens=cfg.max_tokens_thinking),
    }
    for mode in ("direct", "thinking"):
        results[mode]["correct"] = results[mode]["prediction"] == gold

    (cfg.output_dir / "parity-check.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in results.items() if k not in ("direct", "thinking")} | {
        "direct_summary": {k: v for k, v in results["direct"].items() if k not in ("reasoning", "content")},
        "thinking_summary": {k: v for k, v in results["thinking"].items() if k not in ("reasoning", "content")},
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
