"""Load the exp-001 candidate SFT pools into the local Argilla review UI.

This script is deliberately one-way: it never modifies canonical candidate CSVs.
Reviewer changes stay in Argilla until ``export_reviews.py`` writes a separate
review artifact keyed by the stable candidate ID.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import argilla as rg


ROOT = Path(__file__).resolve().parents[2]
DATASET_NAME = "exp-001-response-style-candidates-v2"
DEFAULT_WORKSPACE = "sft-review"
CANDIDATE_FILES = (
    "bare_gec.csv",
    "bare_qa_span.csv",
    "terse_summary.csv",
    "numeric_entity_precision_qa.csv",
    "open_ended_counterexample.csv",
)
RULES = {
    "bare_gec": "Fix only the intended error. Do not explain, over-correct, or change meaning.",
    "bare_qa_span": "Return the shortest answer span literally supported by the passage.",
    "terse_summary": "Use exactly one sentence. Preserve the key fact without invention or distortion.",
    "numeric_entity_precision_qa": "Return the correct entity or number, not a nearby distractor.",
    "open_ended_counterexample": "The request must be genuinely open-ended; answer helpfully and naturally, without padding, repetition, or unsafe advice.",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_messages(raw: str, source: Path, row_number: int) -> tuple[str, str]:
    try:
        messages = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{source.name}:{row_number}: invalid messages JSON") from exc
    if not isinstance(messages, list) or len(messages) != 2:
        raise ValueError(f"{source.name}:{row_number}: expected exactly two messages")
    user, assistant = messages
    if user.get("role") != "user" or assistant.get("role") != "assistant":
        raise ValueError(f"{source.name}:{row_number}: expected user then assistant")
    if not isinstance(user.get("content"), str) or not isinstance(assistant.get("content"), str):
        raise ValueError(f"{source.name}:{row_number}: expected string content")
    return user["content"], assistant["content"]


def load_candidates(source_csv: Path | None = None) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    inventory: dict[str, dict[str, Any]] = {}
    seen_ids: set[str] = set()
    sources = [(ROOT / file_name, file_name) for file_name in CANDIDATE_FILES] if source_csv is None else [(source_csv, source_csv.name)]
    for path, file_name in sources:
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise ValueError(f"{file_name}: no rows")
        inventory[file_name] = {"rows": len(rows), "sha256": sha256(path)}
        for row_number, row in enumerate(rows, start=2):
            candidate_id = row.get("id", "").strip()
            category = row.get("category", "").strip()
            if not candidate_id or candidate_id in seen_ids:
                raise ValueError(f"{file_name}:{row_number}: missing or duplicate candidate id")
            if category not in RULES:
                raise ValueError(f"{file_name}:{row_number}: unsupported category {category!r}")
            seen_ids.add(candidate_id)
            user_input, target = parse_messages(row["messages"], path, row_number)
            records.append(
                {
                    "id": candidate_id,
                    "fields": {
                        "review_rule": RULES[category],
                        "user_input": user_input,
                        "candidate_target": target,
                    },
                    "metadata": {"category": category, "source_file": file_name},
                    "target": target,
                }
            )
    return records, inventory


def build_settings(source_options: list[str] | None = None) -> rg.Settings:
    return rg.Settings(
        guidelines=(
            "Review every example as potential SFT data. Read the category rule, prompt, and candidate target. "
            "Submit the target unchanged when it is good; otherwise rewrite it directly. "
            "Use Reviewed prompt only when the prompt itself needs repair. The canonical candidate CSVs are never edited by this UI."
        ),
        fields=[
            rg.TextField(name="review_rule", title="Category rule", use_markdown=False),
            rg.TextField(name="user_input", title="User input", use_markdown=False),
            rg.TextField(name="candidate_target", title="Current candidate target", use_markdown=False),
        ],
        questions=[
            rg.TextQuestion(
                name="reviewed_user_input",
                title="Reviewed prompt (edit only if needed)",
                description="Leave blank when the prompt is good. If it is implausible, unclear, or otherwise wrong, enter the corrected full prompt.",
                required=False,
                use_markdown=False,
            ),
            rg.TextQuestion(
                name="reviewed_target",
                title="Reviewed target",
                description="Accept the suggested target unchanged or edit it directly, then submit.",
                required=True,
                use_markdown=False,
            ),
            rg.TextQuestion(
                name="review_note",
                title="Optional review note",
                description="Use only when a short rationale will help later analysis.",
                required=False,
                use_markdown=False,
            ),
        ],
        metadata=[
            rg.TermsMetadataProperty(name="category", options=list(RULES)),
            rg.TermsMetadataProperty(name="source_file", options=source_options or list(CANDIDATE_FILES)),
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true", help="Delete and re-import the Argilla dataset. This deletes UI reviews.")
    parser.add_argument("--dataset-name", default=DATASET_NAME)
    parser.add_argument("--source-csv", type=Path, help="Import one reviewed/pending CSV instead of all raw candidate pools.")
    parser.add_argument("--api-url", default=os.getenv("ARGILLA_API_URL", "http://127.0.0.1:6900"))
    parser.add_argument("--api-key", default=os.getenv("ARGILLA_API_KEY", "argilla.apikey"))
    parser.add_argument("--workspace", default=os.getenv("ARGILLA_WORKSPACE", DEFAULT_WORKSPACE))
    args = parser.parse_args()

    source_records, inventory = load_candidates(args.source_csv)
    client = rg.Argilla(api_url=args.api_url, api_key=args.api_key)
    existing = client.datasets(name=args.dataset_name, workspace=args.workspace)
    if existing is not None:
        if not args.replace:
            raise SystemExit(
                f"Argilla dataset {args.dataset_name!r} already exists. It was not changed. "
                "Use export_reviews.py first; use --replace only to intentionally discard UI reviews."
            )
        existing.delete()

    dataset = rg.Dataset(
        name=args.dataset_name,
        workspace=args.workspace,
        settings=build_settings(list(inventory)),
        client=client,
    )
    dataset.create()
    argilla_records = [
        rg.Record(
            id=item["id"],
            fields=item["fields"],
            metadata=item["metadata"],
            suggestions=[
                rg.Suggestion(value=item["fields"]["user_input"], question_name="reviewed_user_input", agent="candidate-prompt"),
                rg.Suggestion(value=item["target"], question_name="reviewed_target", agent="candidate-target"),
            ],
        )
        for item in source_records
    ]
    dataset.records.log(argilla_records, batch_size=100)
    print(json.dumps({"dataset": args.dataset_name, "workspace": args.workspace, "records": len(argilla_records), "source_inventory": inventory}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
