"""Validate and freeze the exp-005 final holdout manifest."""
from __future__ import annotations

import csv
import hashlib
import json
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path


HERE = Path(__file__).resolve().parent
HOLDOUT = HERE / "evaluation" / "final-holdout-v1.csv"
RUBRIC = HERE / "evaluation" / "scoring-rubric.md"
MANIFEST = HERE / "evaluation" / "manifest.json"
CORE = HERE.parent / "exp-001-sft-dataset" / "clean-v2" / "sft-clean-v2-800.csv"
TARGETED = HERE / "data" / "targeted-reviewed-60.jsonl"
PRECISION_V2 = HERE / "data" / "precision-v2-candidates.jsonl"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def user_from_messages(raw: str) -> str:
    messages = json.loads(raw)
    return next(item["content"] for item in messages if item["role"] == "user")


def main() -> None:
    with HOLDOUT.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "id", "split", "capability_family", "prompt_tr", "expected_response_mode",
        "required_content", "disallowed_behavior", "status",
    }
    if set(rows[0]) != required or len(rows) != 48:
        raise ValueError("Holdout must contain the exact schema and 48 records")
    if len({row["id"] for row in rows}) != 48:
        raise ValueError("Duplicate holdout IDs")
    prompts = [normalize(row["prompt_tr"]) for row in rows]
    if len(set(prompts)) != 48:
        raise ValueError("Duplicate normalized holdout prompts")
    if any(row["split"] != "final" or row["status"] != "ready" for row in rows):
        raise ValueError("Every holdout row must be final/ready")
    if any(not all(row[column].strip() for column in required) for row in rows):
        raise ValueError("Holdout contains an empty required value")

    training_prompts: list[tuple[str, str]] = []
    with CORE.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            training_prompts.append((row["id"], normalize(user_from_messages(row["messages"]))))
    for path in (TARGETED, PRECISION_V2):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                training_prompts.append((row["id"], normalize(row["user_input"])))

    exact = []
    suspicious = []
    for row, prompt in zip(rows, prompts):
        for train_id, train_prompt in training_prompts:
            if prompt == train_prompt:
                exact.append({"holdout_id": row["id"], "training_id": train_id})
                continue
            score = SequenceMatcher(None, prompt, train_prompt).ratio()
            if score >= 0.82:
                suspicious.append(
                    {"holdout_id": row["id"], "training_id": train_id, "similarity": round(score, 4)}
                )
    if exact:
        raise ValueError(f"Exact training/holdout overlap: {exact}")

    manifest = {
        "version": "final-policy-holdout-v1",
        "role": "sealed-final-test",
        "rows": len(rows),
        "family_counts": dict(sorted(Counter(row["capability_family"] for row in rows).items())),
        "validation": {
            "unique_ids": True,
            "unique_normalized_prompts": True,
            "exact_training_overlap": 0,
            "near_match_review_threshold": 0.82,
            "near_match_candidates": suspicious,
        },
        "use_policy": (
            "Freeze before training. Do not use outputs to change exp-005 data, hyperparameters, "
            "or checkpoint selection. Evaluate only after the candidate is frozen."
        ),
        "artifacts": {
            "holdout": {"path": HOLDOUT.name, "sha256": sha256(HOLDOUT)},
            "rubric": {"path": RUBRIC.name, "sha256": sha256(RUBRIC)},
        },
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
