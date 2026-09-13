#!/usr/bin/env python3
"""Check an lm-eval-harness MC/log-likelihood samples file for position bias.

Flags the same failure mode found in belebele_tr: does one answer position
dominate the model's argmax log-likelihood regardless of content, far more
often than the gold-answer distribution would predict by chance?

Usage: python analyze_mc_bias.py path/to/samples_<task>_<timestamp>.jsonl
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from string import ascii_uppercase


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: analyze_mc_bias.py <samples_jsonl_path>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    with path.open(encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]

    if not rows or "resps" not in rows[0]:
        print(f"{path.name}: not a log-likelihood MC samples file (no 'resps' field), skipping")
        return 0

    n_choices = len(rows[0]["resps"])
    letters = ascii_uppercase[:n_choices]

    pred_letters = []
    gold_letters = []
    position_logprobs = {L: [] for L in letters}

    for r in rows:
        logprobs = [float(r["resps"][i][0][0]) for i in range(n_choices)]
        pred_idx = max(range(n_choices), key=lambda i: logprobs[i])
        gold_idx = r["target"] if isinstance(r["target"], int) else int(r["target"])
        pred_letters.append(letters[pred_idx])
        gold_letters.append(letters[gold_idx])
        for L, lp in zip(letters, logprobs):
            position_logprobs[L].append(lp)

    n = len(rows)
    pred_dist = Counter(pred_letters)
    gold_dist = Counter(gold_letters)
    acc = sum(p == g for p, g in zip(pred_letters, gold_letters)) / n

    print(f"file: {path.name}")
    print(f"n_choices: {n_choices}, n_items: {n}")
    print(f"accuracy: {acc:.4f}")
    print(f"predicted distribution: {dict(pred_dist)}")
    print(f"gold distribution: {dict(gold_dist)}")
    for L in letters:
        vals = position_logprobs[L]
        mean = sum(vals) / len(vals)
        print(f"  position {L}: mean logprob = {mean:.3f}, argmax rate = {pred_dist.get(L, 0)}/{n} = {pred_dist.get(L, 0)/n:.1%}")

    max_rate = max(pred_dist.values()) / n
    expected_max_rate = max(gold_dist.values()) / n
    if max_rate > 0.6 and max_rate > expected_max_rate * 1.5:
        dominant = max(pred_dist, key=pred_dist.get)
        print(f"BIAS FLAG: position {dominant} dominates predictions ({max_rate:.1%}) far more than gold distribution would predict ({expected_max_rate:.1%}) -- likely the same scoring artifact as belebele_tr.")
    else:
        print("No strong position collapse detected.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
