#!/usr/bin/env python3
"""Freeze the submitted subset of the intentionally stopped final review."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import argilla as rg

ROOT = Path(__file__).parent
OUT = ROOT / "evaluation" / "argilla-partial-review-16.jsonl"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    client = rg.Argilla(
        api_url=os.getenv("ARGILLA_API_URL", "http://127.0.0.1:6900"),
        api_key=os.getenv("ARGILLA_API_KEY", "argilla.apikey"),
    )
    dataset = client.datasets(name="exp-005-final-blind-review", workspace="sft-review")
    rows = []
    status_counts: dict[str, int] = {}
    for record in dataset.records:
        status = str(record.status)
        status_counts[status] = status_counts.get(status, 0) + 1
        if status != "completed":
            continue
        responses = {
            response.question_name: response.value
            for response in (record.responses or [])
        }
        rows.append({
            "id": record.id,
            "category": record.fields["category"],
            "prompt_tr": record.fields["prompt_tr"],
            "output_a": record.fields["output_a"],
            "output_b": record.fields["output_b"],
            "pairwise_preference": responses.get("pairwise_preference"),
            "review_notes": responses.get("review_notes", ""),
            "review_status": "completed",
            "identity_mapping_unsealed": False,
        })
    if len(rows) != 16 or status_counts != {"pending": 32, "completed": 16}:
        raise RuntimeError(f"Unexpected frozen review state: rows={len(rows)} statuses={status_counts}")
    with OUT.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest = {
        "dataset_name": dataset.name,
        "dataset_id": str(dataset.id),
        "submitted_records": len(rows),
        "unreviewed_records": status_counts["pending"],
        "interpretation": "directional qualitative diagnostic; not a completed 48-item final score",
        "mapping_status": "sealed-not-used",
        "export_sha256": sha256(OUT),
    }
    (OUT.parent / "argilla-partial-review-16.manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
