#!/usr/bin/env python3
"""Read-only checks for exp-008 candidate drafts and known prompt pools."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODEL = ROOT.parent
CANDIDATES = ROOT / "data" / "candidates-v1.csv"
KNOWN = (
    MODEL / "exp-007-boundary-benchmark" / "development-v1.csv",
    MODEL / "exp-007-boundary-benchmark" / "development-v2.csv",
    MODEL / "exp-006-quality-repair-sft" / "data" / "sft-clean-v4-quality-repair-958.csv",
    MODEL / "exp-006-quality-repair-sft" / "evaluation" / "final-holdout-v2.csv",
    MODEL / "exp-005-targeted-policy-sft" / "evaluation" / "final-holdout-v1.csv",
    MODEL / "exp-002-communication-policy-benchmark" / "test.csv",
    MODEL / "exp-001-sft-dataset" / "reviewed-v3" / "accepted-reviewed.csv",
)
FAMILIES = {
    "hidden_ambiguity",
    "unsupported_completion",
    "turkish_precision",
    "calibrated_emotional",
    "consistency_integrity",
}


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[^\w]+", " ", value).strip()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def prompt(row: dict[str, str]) -> str:
    if row.get("prompt_tr"):
        return row["prompt_tr"]
    return next(
        item["content"]
        for item in json.loads(row["messages"])
        if item["role"] == "user"
    )


def main() -> None:
    candidates = rows(CANDIDATES)
    assert len(candidates) == 100, f"Expected 100 candidates, got {len(candidates)}"
    assert [row["id"] for row in candidates] == [
        f"gen-{index:03d}" for index in range(1, 101)
    ], "Candidate IDs are missing, repeated, or out of sequence"
    assert Counter(row["capability_family"] for row in candidates) == {
        family: 20 for family in FAMILIES
    }, "Candidate family counts are not 20 each"
    assert all(
        row["status"] == "candidate"
        and all(row.get(field, "").strip() for field in (
            "boundary", "register", "prompt_tr", "proposed_response"
        ))
        for row in candidates
    ), "A candidate has a missing field or unexpected status"
    candidate_prompts = [normalized(row["prompt_tr"]) for row in candidates]
    assert len(set(candidate_prompts)) == len(candidate_prompts), "Duplicate candidate prompts"

    prior: dict[str, tuple[str, str]] = {}
    for path in KNOWN:
        for row in rows(path):
            prior.setdefault(normalized(prompt(row)), (path.name, row["id"]))
    overlaps = [
        (row["id"], prior[value])
        for row, value in zip(candidates, candidate_prompts, strict=True)
        if value in prior
    ]
    assert not overlaps, f"Exact normalized prompt overlap: {overlaps}"

    print(json.dumps({
        "status": "candidate-schema-and-exact-overlap-passed",
        "candidate_rows": len(candidates),
        "families": dict(Counter(row["capability_family"] for row in candidates)),
        "hidden_ambiguity_boundaries": dict(Counter(
            row["boundary"] for row in candidates
            if row["capability_family"] == "hidden_ambiguity"
        )),
        "known_prompt_pool": len(prior),
        "exact_normalized_overlaps": len(overlaps),
        "limitation": "Near and conceptual overlap require separate manual review.",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
