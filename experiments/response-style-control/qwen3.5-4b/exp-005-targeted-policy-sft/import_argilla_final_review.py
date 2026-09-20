#!/usr/bin/env python3
"""Import the sealed exp-005 blind A/B review set into local Argilla."""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

import argilla as rg


ROOT = Path(__file__).parent
DEFAULT_INPUT = ROOT / "results" / "blind-review" / "blind-review.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--api-url", default=os.getenv("ARGILLA_API_URL", "http://127.0.0.1:6900"))
    parser.add_argument("--api-key", default=os.getenv("ARGILLA_API_KEY", "argilla.apikey"))
    parser.add_argument("--workspace", default=os.getenv("ARGILLA_WORKSPACE", "sft-review"))
    parser.add_argument("--dataset-name", default="exp-005-final-blind-review")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 48:
        raise ValueError(f"Expected 48 blind-review records, found {len(rows)}")

    client = rg.Argilla(api_url=args.api_url, api_key=args.api_key)
    existing = client.datasets(name=args.dataset_name, workspace=args.workspace)
    if existing is not None:
        if not args.replace:
            raise SystemExit(f"Dataset {args.dataset_name!r} already exists; use --replace intentionally.")
        existing.delete()

    settings = rg.Settings(
        guidelines=(
            "Blind paired final review. Do not infer model identity. Compare correctness, relevance, "
            "clarity, naturalness, and compliance with the frozen scoring rubric. Choose Equal when "
            "neither response is clearly better. Add a note only for a consequential issue."
        ),
        fields=[
            rg.TextField(name="category", title="Capability category", use_markdown=False),
            rg.TextField(name="prompt_tr", title="Prompt", use_markdown=False),
            rg.TextField(name="output_a", title="Response A", use_markdown=False),
            rg.TextField(name="output_b", title="Response B", use_markdown=False),
        ],
        questions=[
            rg.LabelQuestion(
                name="pairwise_preference",
                title="Which response is better overall?",
                labels=["A", "B", "Equal"],
                required=True,
            ),
            rg.TextQuestion(
                name="review_notes",
                title="Optional note (only for an important issue)",
                required=False,
                use_markdown=False,
            ),
        ],
    )
    dataset = rg.Dataset(
        name=args.dataset_name,
        workspace=args.workspace,
        settings=settings,
        client=client,
    )
    dataset.create()
    dataset.records.log(
        [
            rg.Record(
                id=row["id"],
                fields={
                    "category": row["category"],
                    "prompt_tr": row["prompt_tr"],
                    "output_a": row["output_a"],
                    "output_b": row["output_b"],
                },
            )
            for row in rows
        ],
        batch_size=24,
    )
    print(
        f"{args.dataset_name} records={len(rows)} "
        f"url={args.api_url}/dataset/{dataset.id}/annotation-mode?page=1&status=pending"
    )


if __name__ == "__main__":
    main()
