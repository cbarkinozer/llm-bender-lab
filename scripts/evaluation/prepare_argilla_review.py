#!/usr/bin/env python3
"""Add non-decisive automatic diagnostics to the anonymous review CSV."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


SOCIAL_PREAMBLE = re.compile(r"^(?:harika|mükemmel|süper|çok güzel|anlıyorum|haklısınız|haklısın|tebrik|bence)\b", re.I)
ANTHROPOMORPHIC = re.compile(r"\b(?:hissediyorum|üzülürüm|seviyorum|hoşuma gider|benim için|kişisel tercihim|kişisel fikrim)\b", re.I)
GENERIC_CLOSING = re.compile(r"\b(?:umarım yardımcı|başka sorunuz|yardımcı olabilirim|sormaktan çekinmeyin|daha fazla bilgi)\b", re.I)


def diagnostics(text: str) -> dict[str, object]:
    words = re.findall(r"\S+", text, flags=re.UNICODE)
    return {
        "chars": len(text),
        "words": len(words),
        "lines": text.count("\n") + 1 if text else 0,
        "auto_social_preamble": bool(SOCIAL_PREAMBLE.search(text.strip())),
        "auto_anthropomorphic_claim": bool(ANTHROPOMORPHIC.search(text)),
        "auto_generic_closing": bool(GENERIC_CLOSING.search(text)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("input review CSV is empty")

    output_fields = list(rows[0]) + [
        "output_a_chars", "output_b_chars", "output_a_words", "output_b_words",
        "output_a_lines", "output_b_lines", "char_delta_a_minus_b",
        "word_delta_a_minus_b", "char_ratio_a_over_b", "shorter_output",
        "auto_a_social_preamble", "auto_b_social_preamble",
        "auto_a_anthropomorphic_claim", "auto_b_anthropomorphic_claim",
        "auto_a_generic_closing", "auto_b_generic_closing",
        "pairwise_preference", "task_completion_a", "task_completion_b",
        "directness_a", "directness_b", "neutrality_a", "neutrality_b",
        "brevity_a", "brevity_b", "helpfulness_a", "helpfulness_b",
        "judgment_a", "judgment_b", "calibration_a", "calibration_b",
        "non_sycophancy_a", "non_sycophancy_b", "non_anthropomorphism_a",
        "non_anthropomorphism_b", "clarification_discipline_a",
        "clarification_discipline_b", "review_notes",
    ]
    for row in rows:
        a, b = diagnostics(row["output_a"]), diagnostics(row["output_b"])
        a_chars, b_chars = int(a["chars"]), int(b["chars"])
        a_words, b_words = int(a["words"]), int(b["words"])
        row.update({
            "output_a_chars": a_chars, "output_b_chars": b_chars,
            "output_a_words": a_words, "output_b_words": b_words,
            "output_a_lines": a["lines"], "output_b_lines": b["lines"],
            "char_delta_a_minus_b": a_chars - b_chars,
            "word_delta_a_minus_b": a_words - b_words,
            "char_ratio_a_over_b": f"{a_chars / b_chars:.4f}" if b_chars else "",
            "shorter_output": "A" if a_chars < b_chars else "B" if b_chars < a_chars else "tie",
            "auto_a_social_preamble": a["auto_social_preamble"],
            "auto_b_social_preamble": b["auto_social_preamble"],
            "auto_a_anthropomorphic_claim": a["auto_anthropomorphic_claim"],
            "auto_b_anthropomorphic_claim": b["auto_anthropomorphic_claim"],
            "auto_a_generic_closing": a["auto_generic_closing"],
            "auto_b_generic_closing": b["auto_generic_closing"],
        })
        for field in output_fields[len(list(rows[0])):]:
            row.setdefault(field, "")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} anonymous review rows to {args.output}")


if __name__ == "__main__":
    main()
