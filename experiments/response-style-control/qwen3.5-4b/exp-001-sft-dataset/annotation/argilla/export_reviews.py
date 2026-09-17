"""Export submitted Argilla review responses without changing candidate CSVs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path

import argilla as rg


ROOT = Path(__file__).resolve().parents[2]
DATASET_NAME = "exp-001-response-style-candidates-v2"
DEFAULT_WORKSPACE = "sft-review"
OUTPUT_DIR = ROOT / "review-exports"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def submitted_value(record: rg.Record, question_name: str, reviewer_id: str) -> str:
    responses = [
        response
        for response in record.responses[question_name]
        if str(response.user_id) == reviewer_id and response.status == "submitted"
    ]
    if len(responses) > 1:
        raise ValueError(f"{record.id}: multiple submitted {question_name} responses for reviewer {reviewer_id}")
    return "" if not responses else str(responses[0].value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default=os.getenv("ARGILLA_API_URL", "http://127.0.0.1:6900"))
    parser.add_argument("--api-key", default=os.getenv("ARGILLA_API_KEY", "argilla.apikey"))
    parser.add_argument("--workspace", default=os.getenv("ARGILLA_WORKSPACE", DEFAULT_WORKSPACE))
    parser.add_argument("--output", type=Path, help="Default: timestamped file under review-exports/.")
    args = parser.parse_args()

    client = rg.Argilla(api_url=args.api_url, api_key=args.api_key)
    dataset = client.datasets(name=DATASET_NAME, workspace=args.workspace)
    if dataset is None:
        raise SystemExit(f"Dataset {DATASET_NAME!r} not found in workspace {args.workspace!r}.")
    reviewer_id = str(client.me.id)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or OUTPUT_DIR / f"argilla-review-export-{timestamp}.csv"
    output.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for record in dataset.records(with_responses=True):
        reviewed_target = submitted_value(record, "reviewed_target", reviewer_id)
        if not reviewed_target:
            continue
        reviewed_user_input = submitted_value(record, "reviewed_user_input", reviewer_id)
        rows.append(
            {
                "id": record.id,
                "category": record.metadata["category"],
                "source_file": record.metadata["source_file"],
                "candidate_user_input": record.fields["user_input"],
                "reviewed_user_input": reviewed_user_input or record.fields["user_input"],
                "user_input_changed": str(bool(reviewed_user_input)).lower(),
                "candidate_target": record.fields["candidate_target"],
                "reviewed_target": reviewed_target,
                "review_note": submitted_value(record, "review_note", reviewer_id),
                "reviewer_argilla_user_id": reviewer_id,
            }
        )
    rows.sort(key=lambda row: row["id"])
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["id", "category", "source_file", "candidate_user_input", "reviewed_user_input", "user_input_changed", "candidate_target", "reviewed_target", "review_note", "reviewer_argilla_user_id"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Exported {len(rows)} submitted reviews to {output}")
    print(f"sha256={sha256(output)}")


if __name__ == "__main__":
    main()
