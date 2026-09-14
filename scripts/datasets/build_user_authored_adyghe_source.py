#!/usr/bin/env python3
"""Normalize the user-authored Adyghe source into model-neutral records."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_SHA256 = "70edc807e964cc249282b0a0201eb70be7dcdad401825b761a22d84f0156e810"
CORRECTIONS = {
    24: ("Х х", "h / kh", "Corrects the conflicting `kğ` transliteration; aligns with source line 45."),
    79: ("Мыр", "this", "Removes a display-only HTML entity from the Adyghe text."),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def category(line_number: int) -> str:
    if 3 <= line_number <= 47:
        return "orthography_romanization"
    if 48 <= line_number <= 71:
        return "phrase_translation"
    if 72 <= line_number <= 161:
        return "lexicon"
    if 162 <= line_number <= 170:
        return "parallel_text"
    if 172 <= line_number <= 195:
        return "story_lexicon"
    raise ValueError(f"unexpected data row at line {line_number}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--audit-json", type=Path, required=True)
    args = parser.parse_args()

    if digest(args.source) != EXPECTED_SHA256:
        raise ValueError("source SHA-256 differs from the pinned user-authored v0.1 input")

    rows = []
    corrections_applied = []
    for line_number, line in enumerate(args.source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 2:
            raise ValueError(f"line {line_number}: expected exactly two TSV columns")
        adyghe, gloss = (field.strip() for field in fields)
        correction = None
        if line_number in CORRECTIONS:
            adyghe, gloss, correction = CORRECTIONS[line_number]
            corrections_applied.append({"source_line": line_number, "reason": correction})
        rows.append(
            {
                "id": f"user-authored-adyghe-v0.1-{line_number:03d}",
                "source_line": line_number,
                "category": category(line_number),
                "adyghe": adyghe,
                "gloss_or_romanization": gloss,
                "provenance": "user-authored",
                "correction": correction,
            }
        )

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    args.output_jsonl.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8"
    )
    audit = {
        "dataset": "user-authored-adyghe-source",
        "version": "v0.1",
        "source_sha256": digest(args.source),
        "record_count": len(rows),
        "corrections_applied": corrections_applied,
        "output_sha256": digest(args.output_jsonl),
        "training_use": "allowed_by_data_author",
        "evaluation_interpretation": "AdygheBench derived from this source measures curriculum mastery, not unseen-data generalization.",
    }
    args.audit_json.parent.mkdir(parents=True, exist_ok=True)
    args.audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
