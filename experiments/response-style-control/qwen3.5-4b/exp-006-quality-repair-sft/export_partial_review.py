#!/usr/bin/env python3
"""Export one fully completed exp-006 Argilla category without finalizing exp-006."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

import argilla as rg


ROOT = Path(__file__).parent
CANDIDATES = ROOT / "data" / "quality-repair-candidates-100.jsonl"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", required=True)
    args = parser.parse_args()

    candidates = [
        json.loads(line)
        for line in CANDIDATES.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    selected = [row for row in candidates if row["category"] == args.category]
    if not selected:
        raise ValueError(f"Unknown category: {args.category}")
    candidates_by_id = {row["id"]: row for row in selected}

    client = rg.Argilla(
        api_url=os.getenv("ARGILLA_API_URL", "http://127.0.0.1:6900"),
        api_key=os.getenv("ARGILLA_API_KEY", "argilla.apikey"),
    )
    dataset = client.datasets(
        name=f"exp-006-{args.category.replace('_', '-')}", workspace="sft-review"
    )
    if dataset is None:
        raise RuntimeError(f"Argilla dataset is missing for {args.category}")

    status_counts: Counter[str] = Counter()
    reviewed = []
    for record in dataset.records:
        status = str(record.status)
        status_counts[status] += 1
        if record.id not in candidates_by_id:
            raise ValueError(f"Unexpected record ID: {record.id}")
        if status != "completed":
            continue
        answers = {
            response.question_name: response.value
            for response in (record.responses or [])
        }
        decision = answers.get("decision")
        rewritten = (answers.get("rewritten_response") or "").strip()
        if decision not in {"accept", "rewrite", "reject"}:
            raise ValueError(f"Missing or invalid decision: {record.id}")
        if decision == "rewrite" and not rewritten:
            raise ValueError(f"Rewrite has no replacement response: {record.id}")
        source = candidates_by_id[record.id]
        reviewed.append(
            {
                **source,
                "review_decision": decision,
                "reviewed_response": (
                    rewritten
                    if decision == "rewrite"
                    else source["messages"][1]["content"] if decision == "accept" else ""
                ),
                "failure_tags": answers.get("failure_tags") or [],
                "review_notes": answers.get("review_notes") or "",
                "argilla_dataset_id": str(dataset.id),
                "review_status": "completed",
            }
        )

    reviewed.sort(key=lambda row: row["id"])
    if len(reviewed) != len(selected) or status_counts != Counter(completed=len(selected)):
        raise RuntimeError(
            f"Category review is incomplete: expected={len(selected)} "
            f"completed={len(reviewed)} statuses={dict(status_counts)}"
        )

    output_dir = ROOT / "data" / "partial-reviews"
    output_dir.mkdir(exist_ok=True)
    stem = f"{args.category.replace('_', '-')}-reviewed-{len(reviewed)}"
    output = output_dir / f"{stem}.jsonl"
    with output.open("w", encoding="utf-8") as handle:
        for row in reviewed:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "status": "completed-category-review; experiment-review-still-in-progress",
        "category": args.category,
        "dataset_name": dataset.name,
        "dataset_id": str(dataset.id),
        "candidate_records": len(selected),
        "reviewed_records": len(reviewed),
        "decisions": dict(Counter(row["review_decision"] for row in reviewed)),
        "artifacts": {
            "candidate_pool": {
                "path": str(CANDIDATES.relative_to(ROOT)),
                "sha256": sha256(CANDIDATES),
            },
            "review_export": {"path": output.name, "sha256": sha256(output)},
        },
        "scope": "This is a durable category-level review export, not an exp-006 training artifact or experiment finalization.",
    }
    manifest_path = output_dir / f"{stem}.manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
