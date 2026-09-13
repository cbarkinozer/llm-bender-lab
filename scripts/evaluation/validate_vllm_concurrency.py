#!/usr/bin/env python3
"""Spot-check that concurrent requests give the same *answer* as sequential ones.

Continuous batching means multiple in-flight requests share GPU kernels; matmul
reduction order can differ from the single-request case, which empirically
does change exact generated text/token counts at concurrency>1 (observed on
this host: 2/4 items diverged in raw text at concurrency=16). That divergence
is tolerated the same way it already is between the Transformers and vLLM
sequential backends -- this project's protocol compares extracted FINAL:X
predictions and correctness, not byte-exact generation. This script therefore
fails loudly only on a *prediction*-level mismatch (different extracted answer
or different correctness), not on text/reasoning differences, and reports the
raw text divergence rate as informational context.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(script: Path, mode: str, start_index: int, limit: int, max_new_tokens: int, concurrency: int, port: int, out_dir: Path) -> list[dict]:
    subprocess.run(
        [
            sys.executable, str(script),
            "--output-dir", str(out_dir), "--mode", mode,
            "--start-index", str(start_index), "--limit", str(limit),
            "--max-new-tokens", str(max_new_tokens), "--concurrency", str(concurrency),
            "--port", str(port),
        ],
        check=True, stdout=subprocess.DEVNULL,
    )
    rows = [json.loads(line) for line in (out_dir / "samples.jsonl").read_text(encoding="utf-8").splitlines()]
    return sorted(rows, key=lambda r: r["index"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=("direct", "thinking"))
    parser.add_argument("--start-index", type=int, required=True)
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--max-new-tokens", type=int, required=True)
    parser.add_argument("--concurrency", type=int, required=True)
    parser.add_argument("--port", type=int, default=8000)
    cfg = parser.parse_args()

    script = Path(__file__).with_name("evaluate_belebele_generation_vllm.py")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        seq_rows = run(script, cfg.mode, cfg.start_index, cfg.limit, cfg.max_new_tokens, 1, cfg.port, tmp_path / "seq")
        conc_rows = run(script, cfg.mode, cfg.start_index, cfg.limit, cfg.max_new_tokens, cfg.concurrency, cfg.port, tmp_path / "conc")

    prediction_mismatches = []
    text_divergences = []
    for seq, conc in zip(seq_rows, conc_rows):
        text_differs = seq["answer_text"] != conc["answer_text"] or seq["reasoning"] != conc["reasoning"]
        prediction_differs = seq["prediction"] != conc["prediction"] or seq["correct"] != conc["correct"]
        entry = {
            "index": seq["index"],
            "sequential": {"prediction": seq["prediction"], "correct": seq["correct"], "generated_tokens": seq["generated_tokens"], "answer_text": seq["answer_text"][:200]},
            "concurrent": {"prediction": conc["prediction"], "correct": conc["correct"], "generated_tokens": conc["generated_tokens"], "answer_text": conc["answer_text"][:200]},
        }
        if text_differs:
            text_divergences.append(entry)
        if prediction_differs:
            prediction_mismatches.append(entry)

    result = {
        "mode": cfg.mode, "items_checked": len(seq_rows), "concurrency_tested": cfg.concurrency,
        "prediction_match": len(prediction_mismatches) == 0,
        "prediction_mismatches": prediction_mismatches,
        "text_divergence_rate": len(text_divergences) / len(seq_rows) if seq_rows else 0.0,
        "text_divergences_note": "expected/tolerated -- raw generated text can differ between concurrency levels the same way it differs between backends; only prediction_mismatches gates this script's exit code",
        "text_divergences": text_divergences,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["prediction_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
