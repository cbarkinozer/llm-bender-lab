#!/usr/bin/env python3
"""Validate the frozen exp-006 human-reviewed tranche and combined SFT artifact."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parent
DATA = ROOT / "data"
EXPECTED = {
    "calibrated_emotional": 20,
    "consistency_integrity": 20,
    "hidden_ambiguity": 20,
    "turkish_precision": 20,
    "unsupported_completion": 20,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def normalized(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    candidates = {
        row["id"]: row
        for row in map(
            json.loads,
            (DATA / "quality-repair-candidates-100.jsonl")
            .read_text(encoding="utf-8")
            .splitlines(),
        )
    }
    reviewed_path = DATA / "quality-repair-reviewed-100.jsonl"
    reviewed = list(
        map(json.loads, reviewed_path.read_text(encoding="utf-8").splitlines())
    )
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    combined_path = DATA / manifest["artifacts"]["combined"]["path"]
    with combined_path.open(encoding="utf-8", newline="") as handle:
        combined = list(csv.DictReader(handle))

    assert len(candidates) == len(reviewed) == 100
    assert len({row["id"] for row in reviewed}) == 100
    assert {row["id"] for row in reviewed} == set(candidates)
    assert Counter(row["category"] for row in reviewed) == Counter(EXPECTED)
    assert all(row["review_decision"] in {"accept", "rewrite", "reject"} for row in reviewed)

    accepted = [row for row in reviewed if row["review_decision"] != "reject"]
    responses = [row["reviewed_response"].strip() for row in accepted]
    assert all(responses)
    assert all(len(response) <= 600 for response in responses)
    assert all(response[-1] in ".?!" for response in responses)
    assert not any("\ufffd" in response for response in responses)
    assert len({normalized(response) for response in responses}) == len(responses)
    assert not any(re.search(r"(^|\n)\s*(#{1,6}|[-*]\s)", response) for response in responses)
    assert all("?" in row["reviewed_response"] for row in accepted if row["category"] == "hidden_ambiguity")

    source_fields = (
        "id",
        "category",
        "messages",
        "source",
        "generation_method",
        "language",
        "quality_status",
    )
    for row in reviewed:
        source = candidates[row["id"]]
        assert all(row.get(field) == source.get(field) for field in source_fields), row["id"]

    assert len(combined) == 858 + len(accepted)
    assert len({row["id"] for row in combined}) == len(combined)
    assert sha256(reviewed_path) == manifest["artifacts"]["review_export"]["sha256"]
    assert sha256(combined_path) == manifest["artifacts"]["combined"]["sha256"]
    partial_manifests = sorted((DATA / "partial-reviews").glob("*.manifest.json"))
    assert len(partial_manifests) == 5
    for manifest_path in partial_manifests:
        partial = json.loads(manifest_path.read_text(encoding="utf-8"))
        export_path = manifest_path.parent / partial["artifacts"]["review_export"]["path"]
        assert sha256(export_path) == partial["artifacts"]["review_export"]["sha256"]
        assert sha256(DATA / "quality-repair-candidates-100.jsonl") == partial["artifacts"]["candidate_pool"]["sha256"]

    report = {
        "status": "passed",
        "candidate_rows": len(candidates),
        "reviewed_rows": len(reviewed),
        "accepted_rows": len(accepted),
        "rejected_rows": len(reviewed) - len(accepted),
        "combined_rows": len(combined),
        "categories": dict(Counter(row["category"] for row in reviewed)),
        "decisions": dict(Counter(row["review_decision"] for row in reviewed)),
        "response_characters": {
            "min": min(map(len, responses)),
            "median": sorted(map(len, responses))[len(responses) // 2],
            "max": max(map(len, responses)),
        },
        "checks": {
            "candidate_binding": "passed",
            "category_balance": "passed",
            "nonempty_targets": "passed",
            "unique_targets": "passed",
            "unicode_integrity": "passed",
            "plain_format": "passed",
            "length_limit": "passed",
            "hidden_ambiguity_questions": "passed",
            "combined_id_uniqueness": "passed",
            "artifact_hashes": "passed",
            "category_export_hashes": "passed",
        },
        "manual_qa": {
            "full_tranche_read": True,
            "human_approved_post_review_corrections": [
                "hidden_ambiguity-020",
                "turkish_precision-012",
            ],
        },
    }
    output = ROOT / "evaluation" / "reviewed-quality-report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
