#!/usr/bin/env python3
"""Replace the review workspace with one Argilla dataset per clean SFT category."""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

import argilla as rg

CATEGORIES = ["bare_gec", "bare_qa_span", "terse_summary", "numeric_entity_precision_qa", "open_ended_counterexample"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/clean-v2"))
    parser.add_argument("--api-url", default=os.getenv("ARGILLA_API_URL", "http://127.0.0.1:6900"))
    parser.add_argument("--api-key", default=os.getenv("ARGILLA_API_KEY", "argilla.apikey"))
    parser.add_argument("--workspace", default=os.getenv("ARGILLA_WORKSPACE", "sft-review"))
    args = parser.parse_args()
    client = rg.Argilla(api_url=args.api_url, api_key=args.api_key)
    workspace = client.workspaces(name=args.workspace)
    if workspace is None:
        raise SystemExit(f"Workspace not found: {args.workspace}")

    # The user requested a clean UI. Local exports and source datasets remain
    # untouched; only datasets in this Argilla workspace are replaced.
    for dataset in list(client.datasets.list()):
        if dataset.workspace.name == args.workspace:
            dataset.delete()

    created = []
    for category in CATEGORIES:
        name = f"exp-004-sft-clean-v2-{category}"
        settings = rg.Settings(
            guidelines=(
                f"Category: {category}. Inspect the Turkish input and target carefully. "
                "Mark edit when the target is unnatural, repetitive, too terse, factually wrong, "
                "or does not complete the task. Mark keep only when it is suitable SFT data. "
                "Use notes to write the corrected target or explain the problem."
            ),
            fields=[
                rg.TextField(name="user_input", title="User input", use_markdown=False),
                rg.TextField(name="target", title="Target response", use_markdown=False),
            ],
            questions=[
                rg.LabelQuestion(name="review_status", title="Review status", labels=["keep", "edit", "remove"], required=True),
                rg.TextQuestion(name="review_notes", title="Correction / notes", required=False),
            ],
            metadata=[rg.TermsMetadataProperty(name="category", options=[category])],
        )
        dataset = rg.Dataset(name=name, workspace=args.workspace, settings=settings, client=client)
        dataset.create()
        rows = list(csv.DictReader((args.input_dir / f"{category}.csv").open(encoding="utf-8-sig", newline="")))
        records = []
        for row in rows:
            messages = json.loads(row["messages"])
            records.append(rg.Record(
                id=row["id"],
                fields={"user_input": messages[0]["content"], "target": messages[1]["content"]},
                metadata={"category": category},
            ))
        dataset.records.log(records, batch_size=25)
        created.append({"name": name, "id": str(dataset.id), "records": len(records), "url": f"{args.api_url}/dataset/{dataset.id}/annotation-mode"})
    print(json.dumps({"workspace": args.workspace, "datasets": created}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
