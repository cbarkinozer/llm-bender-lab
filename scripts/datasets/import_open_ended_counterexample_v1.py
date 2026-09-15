"""Import the audited open-ended counterexample candidate pool."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


SOURCE = Path(r"C:\Users\cbark\Downloads\open_ended_counterexample_400.csv")
DESTINATION = Path(__file__).resolve().parents[2] / (
    "experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/"
    "open_ended_counterexample.csv"
)
MANIFEST = DESTINATION.with_suffix(".manifest.json")
SOURCE_SHA256 = "e16b4f061a7e1e9c0e1ad0394dd181770d425b5f980ef7cc9fa01823cb4ae97f"
REQUIRED_COLUMNS = [
    "id", "messages", "category", "answer_type", "domain", "language",
    "source", "source_id", "generator", "generation_prompt_version",
    "reviewer", "quality_status", "rejection_reason", "bareness_check_passed",
    "dedup_cluster_id", "contamination_checked", "contamination_flag", "license",
    "split", "created_at", "notes",
]
BAD_FRAGMENTS = (
    "bağlamında böyle",
    "kararlarında için",
    "sorunlarında için",
    "konularında için",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_as_lf_text(source: Path, destination: Path) -> None:
    text = source.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    destination.write_text(text, encoding="utf-8", newline="\n")


def normalized_sentences(text: str) -> list[str]:
    return [
        re.sub(r"\s+", " ", unicodedata.normalize("NFKC", sentence).lower()).strip()
        for sentence in re.split(r"(?<=[.!?…])\s+", text)
        if sentence.strip()
    ]


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
    if len(rows) != 400 or any(
        row["category"] != "open_ended_counterexample" for row in rows
    ):
        raise RuntimeError("Expected exactly 400 open_ended_counterexample candidate rows.")
    if any(row["quality_status"] != "needs_review" for row in rows):
        raise RuntimeError("Candidate rows must remain marked needs_review.")

    seen_sentences: defaultdict[str, list[str]] = defaultdict(list)
    for row in rows:
        messages = json.loads(row["messages"])
        if len(messages) != 2 or [message.get("role") for message in messages] != [
            "user", "assistant"
        ]:
            raise RuntimeError(f"Invalid two-message conversation: {row['id']}")
        answer = messages[1].get("content", "")
        if not isinstance(answer, str) or any(fragment in answer.lower() for fragment in BAD_FRAGMENTS):
            raise RuntimeError(f"Invalid or malformed target: {row['id']}")
        for sentence in normalized_sentences(answer):
            seen_sentences[sentence].append(row["id"])
    if any(len(ids) > 1 for ids in seen_sentences.values()):
        raise RuntimeError("Exact assistant-sentence duplicates remain in the candidate pool.")

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
        "import_validation": {
            "valid_two_message_rows": len(rows),
            "exact_repeated_assistant_sentences": 0,
            "known_malformed_health_fragments": 0,
        },
        "note": "Candidate pool only; do not train until final combined review and validation.",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
