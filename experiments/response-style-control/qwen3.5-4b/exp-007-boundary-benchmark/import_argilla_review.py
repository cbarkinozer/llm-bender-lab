#!/usr/bin/env python3
"""Create a separate benchmark-authoring review queue, preserving existing reviews."""
import argparse
import csv
import json
import os
from pathlib import Path

import argilla as rg


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=root / "development-v2.csv")
    parser.add_argument("--dataset-name", default="exp-007-boundary-benchmark-v2-review")
    parser.add_argument("--ids", nargs="+", help="Optionally import only changed benchmark IDs")
    args = parser.parse_args()
    client = rg.Argilla(api_url=os.getenv("ARGILLA_API_URL", "http://127.0.0.1:6900"), api_key=os.getenv("ARGILLA_API_KEY", "argilla.apikey"))
    name = args.dataset_name
    dataset = client.datasets(name=name, workspace="sft-review")
    if dataset is None:
        settings = rg.Settings(
            guidelines="Review benchmark design, not model responses or training targets. Check natural Turkish, clear answerability, the rule and its exceptions, a fair scoring anchor, and conceptual independence from training. Accept, rewrite, or reject. For rewrite, provide the full corrected prompt and scoring condition in the relevant fields. These prompts remain development diagnostics.",
            fields=[rg.TextField(name=field, use_markdown=False) for field in ("prompt_tr", "capability_family", "contrast", "expected_mode", "pass_condition")],
            questions=[rg.LabelQuestion(name="decision", labels=["accept", "rewrite", "reject"], required=True),
                       rg.TextQuestion(name="rewritten_prompt", required=False),
                       rg.TextQuestion(name="rewritten_pass_condition", required=False),
                       rg.TextQuestion(name="review_notes", required=False)])
        dataset = rg.Dataset(name=name, workspace="sft-review", settings=settings, client=client).create()
        with args.csv.open(encoding="utf-8", newline="") as handle:
            records = list(csv.DictReader(handle))
        if args.ids:
            records = [row for row in records if row["id"] in args.ids]
            if {row["id"] for row in records} != set(args.ids):
                raise ValueError("Some requested benchmark IDs are missing")
        dataset.records.log([rg.Record(id=row["id"], fields={field: row[field] for field in ("prompt_tr", "capability_family", "contrast", "expected_mode", "pass_condition")}) for row in records])
    print(json.dumps({"name": dataset.name, "records": len(list(dataset.records)), "url": f"http://127.0.0.1:6900/dataset/{dataset.id}/annotation-mode"}, indent=2))


if __name__ == "__main__":
    main()
