#!/usr/bin/env python3
"""Paired direct-vs-thinking analysis over matched Belebele items (McNemar's test).

Reads two samples.jsonl files produced by the same frozen item set (same
document_sha256 per index) and compares correctness per item. Reports parser
success and truncation separately per mode, since a valid comparison must not
conflate "wrong answer" with "failed to parse" or "hit the token cap".
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict[int, dict]:
    rows = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            rows[row["index"]] = row
    return rows


def mcnemar(b: int, c: int) -> dict:
    if b + c == 0:
        return {"statistic": 0.0, "note": "no discordant pairs"}
    statistic = (abs(b - c) - 1) ** 2 / (b + c)
    return {"statistic": statistic, "b_direct_correct_thinking_wrong": b, "c_direct_wrong_thinking_correct": c, "note": "continuity-corrected; compare to chi2(1) critical value 3.841 at alpha=0.05"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--direct-samples", required=True, type=Path)
    parser.add_argument("--thinking-samples", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    cfg = parser.parse_args()

    direct = load(cfg.direct_samples)
    thinking = load(cfg.thinking_samples)
    shared_indices = sorted(set(direct) & set(thinking))
    mismatched_docs = [i for i in shared_indices if direct[i]["document_sha256"] != thinking[i]["document_sha256"]]
    if mismatched_docs:
        raise ValueError(f"document_sha256 mismatch at indices {mismatched_docs}; direct/thinking were not run over the same frozen items")

    both_correct = both_wrong = direct_only = thinking_only = 0
    direct_unparsed = thinking_unparsed = direct_truncated = thinking_truncated = 0
    for i in shared_indices:
        d, t = direct[i], thinking[i]
        direct_unparsed += int(d["prediction"] is None)
        thinking_unparsed += int(t["prediction"] is None)
        direct_truncated += int(d["hit_max_new_tokens"])
        thinking_truncated += int(t["hit_max_new_tokens"])
        if d["correct"] and t["correct"]:
            both_correct += 1
        elif not d["correct"] and not t["correct"]:
            both_wrong += 1
        elif d["correct"] and not t["correct"]:
            direct_only += 1
        else:
            thinking_only += 1

    n = len(shared_indices)
    result = {
        "protocol": "belebele-turkish-paired-analysis-v1",
        "items_compared": n,
        "accuracy": {
            "direct": sum(direct[i]["correct"] for i in shared_indices) / n,
            "thinking": sum(thinking[i]["correct"] for i in shared_indices) / n,
        },
        "parser_failure_rate": {"direct": direct_unparsed / n, "thinking": thinking_unparsed / n},
        "truncation_rate": {"direct": direct_truncated / n, "thinking": thinking_truncated / n},
        "contingency_table": {"both_correct": both_correct, "both_wrong": both_wrong, "direct_correct_thinking_wrong": direct_only, "direct_wrong_thinking_correct": thinking_only},
        "mcnemar": mcnemar(direct_only, thinking_only),
        "caveat": "Truncated/unparsed items are scored as incorrect above like any wrong answer; check truncation_rate before trusting the accuracy delta as a measure of reasoning quality rather than token-budget sufficiency.",
    }
    cfg.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
