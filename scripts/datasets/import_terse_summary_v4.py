"""Import the reviewed-pending terse-summary v4 candidate into the experiment."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


SOURCE = Path(r"C:\Users\cbark\Downloads\terse_summary_500.csv")
DESTINATION = Path(__file__).resolve().parents[2] / (
    "experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/terse_summary.csv"
)
MANIFEST = DESTINATION.with_suffix(".manifest.json")
SOURCE_SHA256 = "1f5630f28a8ab3bde0be325c3cb82b3d54663c39ed3cbd047680321f91919826"
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
    if len(rows) != 500 or any(row["category"] != "terse_summary" for row in rows):
        raise RuntimeError("Expected exactly 500 terse_summary candidate rows.")

    copy_as_lf_text(SOURCE, DESTINATION)
    manifest = {
        "artifact": DESTINATION.name,
        "artifact_sha256": sha256(DESTINATION),
        "source_path": str(SOURCE),
        "source_sha256": source_hash,
        "rows": len(rows),
        "dataset_revision": "v4-candidate",
        "quality_status": "needs_review",
        "accepted_count": 0,
        "contamination_checked": "pending",
        "split": "unassigned",
        "note": "Candidate pool only; do not train until final combined review and validation.",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
