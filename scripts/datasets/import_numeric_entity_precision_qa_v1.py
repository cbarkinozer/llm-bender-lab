"""Import the reviewed-pending numeric/entity precision candidate pool."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


SOURCE = Path(r"C:\Users\cbark\Downloads\numeric_entity_precision_qa.csv")
DESTINATION = Path(__file__).resolve().parents[2] / (
    "experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/"
    "numeric_entity_precision_qa.csv"
)
MANIFEST = DESTINATION.with_suffix(".manifest.json")
SOURCE_SHA256 = "14e25533b23a167ae8228bd27cfafe27968e46ae8d246a3ed3f694c4e09c3af1"
REQUIRED_COLUMNS = [
    "id", "messages", "category", "answer_type", "domain", "language",
    "source", "source_id", "generator", "generation_prompt_version",
    "reviewer", "quality_status", "rejection_reason", "bareness_check_passed",
    "dedup_cluster_id", "contamination_checked", "contamination_flag", "license",
    "split", "created_at", "notes",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_as_lf_text(source: Path, destination: Path) -> None:
    text = source.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    destination.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    source_hash = sha256(SOURCE)
    if source_hash != SOURCE_SHA256:
        raise RuntimeError(
            f"Source checksum mismatch: expected {SOURCE_SHA256}, got {source_hash}. "
            "Audit a changed source before importing it."
        )
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != REQUIRED_COLUMNS:
            raise RuntimeError("Source schema does not match the experiment master schema.")
        rows = list(reader)
    if len(rows) != 500 or any(
        row["category"] != "numeric_entity_precision_qa" for row in rows
    ):
        raise RuntimeError("Expected exactly 500 numeric_entity_precision_qa candidate rows.")
    if any(row["quality_status"] != "needs_review" for row in rows):
        raise RuntimeError("Candidate rows must remain marked needs_review.")

    copy_as_lf_text(SOURCE, DESTINATION)
    manifest = {
        "artifact": DESTINATION.name,
        "artifact_sha256": sha256(DESTINATION),
        "source_path": str(SOURCE),
        "source_sha256": source_hash,
        "rows": len(rows),
        "dataset_revision": "v1-candidate",
        "quality_status": "needs_review",
        "accepted_count": 0,
        "contamination_checked": "pending",
        "split": "unassigned",
        "note": "Candidate pool only; do not train until final combined review and validation.",
    }
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
