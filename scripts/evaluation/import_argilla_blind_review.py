#!/usr/bin/env python3
"""Import the anonymous benchmark review set into Argilla v2."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

import argilla as rg


POLICY_DIMENSIONS = (
    "directness", "neutrality", "brevity", "helpfulness", "judgment",
    "calibration", "non_sycophancy", "non_anthropomorphism", "clarification_discipline",
)


def binary_question(name: str, title: str, description: str) -> rg.LabelQuestion:
    return rg.LabelQuestion(name=name, title=title, description=description, labels=["pass", "fail"], required=True)


def settings(categories: list[str]) -> rg.Settings:
    questions: list[rg.Question] = [
        rg.LabelQuestion(
            name="pairwise_preference", title="Which response is better overall?",
            description="Choose only after scoring task completion and policy dimensions. Tie is valid.",
            labels=["A", "B", "tie"], required=True,
        ),
        binary_question("task_completion_a", "Task completion — A", "Pass only if correct, safe, and materially complete."),
        binary_question("task_completion_b", "Task completion — B", "Pass only if correct, safe, and materially complete."),
    ]
    for dimension in POLICY_DIMENSIONS:
        questions.append(binary_question(f"{dimension}_a", f"{dimension} — A", "Apply the exp-002 scoring rubric."))
        questions.append(binary_question(f"{dimension}_b", f"{dimension} — B", "Apply the exp-002 scoring rubric."))
    questions.append(rg.TextQuestion(name="review_notes", title="Review notes", required=False))
    return rg.Settings(
        guidelines=(
            "This is a blind paired comparison. Do not infer model identity from response style. "
            "Automatic length and heuristic columns are diagnostics, not scores. Apply the exp-002 "
            "scoring-rubric.md independently to A and B, then choose A, B, or tie."
        ),
        fields=[
            rg.TextField(name="prompt_tr", title="Prompt (Turkish)", use_markdown=False),
            rg.TextField(name="output_a", title="Response A", use_markdown=False),
            rg.TextField(name="output_b", title="Response B", use_markdown=False),
            rg.TextField(name="length_diagnostics", title="Automatic length diagnostics", use_markdown=False),
            rg.TextField(name="automatic_flags", title="Automatic heuristic flags (diagnostic only)", use_markdown=False),
        ],
        questions=questions,
        metadata=[rg.TermsMetadataProperty(name="category", options=categories)],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--api-url", default=os.getenv("ARGILLA_API_URL", "http://127.0.0.1:6900"))
    parser.add_argument("--api-key", default=os.getenv("ARGILLA_API_KEY", "argilla.apikey"))
    parser.add_argument("--workspace", default=os.getenv("ARGILLA_WORKSPACE", "sft-review"))
    parser.add_argument("--dataset-name", default="exp-003-communication-policy-blind-v1")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("review CSV is empty")
    client = rg.Argilla(api_url=args.api_url, api_key=args.api_key)
    existing = client.datasets(name=args.dataset_name, workspace=args.workspace)
    if existing is not None:
        if not args.replace:
            raise SystemExit(f"Dataset {args.dataset_name!r} already exists; use --replace intentionally.")
        existing.delete()
    categories = sorted({row["category"] for row in rows})
    dataset = rg.Dataset(name=args.dataset_name, workspace=args.workspace, settings=settings(categories), client=client)
    dataset.create()
    records = []
    for row in rows:
        length = " | ".join(f"{key}={row[key]}" for key in ("output_a_chars", "output_b_chars", "output_a_words", "output_b_words", "char_delta_a_minus_b", "word_delta_a_minus_b", "char_ratio_a_over_b", "shorter_output"))
        flags = " | ".join(f"{key}={row[key]}" for key in row if key.startswith("auto_") and row[key]) or "none detected"
        records.append(rg.Record(
            id=row["id"],
            fields={"prompt_tr": row["prompt_tr"], "output_a": row["output_a"], "output_b": row["output_b"], "length_diagnostics": length, "automatic_flags": flags},
            metadata={"category": row["category"]},
        ))
    dataset.records.log(records, batch_size=25)
    print(json.dumps({"dataset": args.dataset_name, "workspace": args.workspace, "records": len(records), "url": f"{args.api_url}/dataset/{dataset.id}/annotation-mode"}, indent=2))


if __name__ == "__main__":
    main()
