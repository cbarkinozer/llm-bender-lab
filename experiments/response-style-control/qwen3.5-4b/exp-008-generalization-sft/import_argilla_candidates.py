#!/usr/bin/env python3
"""Import exp-008 draft response pairs for explicit human review."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

import argilla as rg


ROOT = Path(__file__).resolve().parent
FILENAME = ROOT / "data" / "candidates-v1.csv"


def settings() -> rg.Settings:
    return rg.Settings(
        guidelines=(
            "These are draft Turkish SFT targets, not benchmark answers. "
            "Check that the prompt is distinct from evaluation scenarios and "
            "that the response is correct, natural, complete, and the right "
            "length. A clarification must be necessary; a direct answer must "
            "not invent facts. Choose rewrite for a repairable target and enter "
            "the complete replacement. Reject an unsuitable prompt."
        ),
        fields=[
            rg.TextField(name="prompt_tr", title="User message", use_markdown=False),
            rg.TextField(name="proposed_response", title="Draft assistant reply", use_markdown=False),
            rg.TextField(name="boundary", title="Decision boundary", use_markdown=False),
            rg.TextField(name="register", title="Register", use_markdown=False),
        ],
        questions=[
            rg.LabelQuestion(
                name="decision", title="Training-data decision",
                labels=["accept", "rewrite", "reject"], required=True,
            ),
            rg.TextQuestion(
                name="rewritten_response",
                title="Full replacement reply (required if rewriting)",
                required=False, use_markdown=False,
            ),
            rg.MultiLabelQuestion(
                name="failure_tags", title="Problems in draft",
                labels=[
                    "incorrect_or_unsupported", "wrong_clarification",
                    "unnatural_turkish", "too_short_or_long",
                    "repetition_or_filler", "semantic_contradiction",
                    "unwarranted_self_state", "benchmark_overlap",
                ], required=False,
            ),
            rg.TextQuestion(
                name="review_notes", title="Optional review note",
                required=False, use_markdown=False,
            ),
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default=os.getenv("ARGILLA_API_URL", "http://127.0.0.1:6900"))
    parser.add_argument("--api-key", default=os.getenv("ARGILLA_API_KEY", "argilla.apikey"))
    parser.add_argument("--workspace", default=os.getenv("ARGILLA_WORKSPACE", "sft-review"))
    args = parser.parse_args()

    with FILENAME.open(encoding="utf-8", newline="") as handle:
        candidates = list(csv.DictReader(handle))
    if len(candidates) != 100:
        raise ValueError(f"Expected 100 draft rows, got {len(candidates)}")

    client = rg.Argilla(api_url=args.api_url, api_key=args.api_key)
    links = []
    families = sorted({row["capability_family"] for row in candidates})
    names = {family: f"exp-008-{family.replace('_', '-')}" for family in families}
    for name in names.values():
        existing = client.datasets(name=name, workspace=args.workspace)
        if existing is not None:
            raise RuntimeError(f"{name} already exists; refusing to replace human review")
    for family in families:
        name = names[family]
        dataset = rg.Dataset(
            name=name, workspace=args.workspace, settings=settings(), client=client,
        )
        dataset.create()
        subset = [row for row in candidates if row["capability_family"] == family]
        dataset.records.log([
            rg.Record(id=row["id"], fields={
                "prompt_tr": row["prompt_tr"],
                "proposed_response": row["proposed_response"],
                "boundary": row["boundary"],
                "register": row["register"],
            }) for row in subset
        ], batch_size=20)
        links.append({
            "dataset": name,
            "rows": len(subset),
            "url": f"{args.api_url}/dataset/{dataset.id}/annotation-mode?page=1&status=pending",
        })
    print(json.dumps(links, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
