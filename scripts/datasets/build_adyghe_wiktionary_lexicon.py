#!/usr/bin/env python3
"""Build a conservative, traceable Adyghe--English lexicon from a TSV export.

The input's first field is a Wiktionary scrape, not a clean lemma field: it
may contain a lemma, inflections, transliterations, and scraped navigation
fragments separated by ``|``.  This builder never edits the source.  It keeps
the raw field, extracts only Cyrillic Adyghe-looking forms for the usable
lemma/variant layer, and records every excluded segment per entry.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from collections import Counter
from pathlib import Path


EXPECTED_SOURCE_SHA256 = "4b7e3bba72a79293d108873afe172cd9ffa3a6da192b781b4d9957b8ca89700d"
UPSTREAM_REPOSITORY = "https://github.com/Vuizur/Wiktionary-Dictionaries"
UPSTREAM_COMMIT = "be0cfb8d614470bc8b9d9006ddff8b921cd5c2e3"
UPSTREAM_PATH = "Adyghe-English Wiktionary dictionary.tsv"
UPSTREAM_LICENSE = "CC-BY-SA-3.0 and GFDL (as declared by the upstream repository)"
CYRILLIC_FORM = re.compile(r"[А-Яа-яЁёӀӏ][А-Яа-яЁёӀӏ -]*")
POS_PATTERN = re.compile(r"<i>(.*?)</i>")
SENSE_PATTERN = re.compile(r"<li>(.*?)</li>", re.DOTALL)
HTML_TAG = re.compile(r"<[^>]+>")
WHITESPACE = re.compile(r"\s+")
ASCII_MULTIWORD = re.compile(r"(?i)[a-z]{2,}\s+[a-z]{2,}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_text(value: str) -> str:
    return WHITESPACE.sub(" ", html.unescape(HTML_TAG.sub(" ", value))).strip()


def extract_cyrillic_form(segment: str) -> str | None:
    """Return the full leading Adyghe-looking Cyrillic form, if one exists."""
    match = CYRILLIC_FORM.match(segment.strip())
    if not match:
        return None
    return match.group(0).strip(" -") or None


def parse_row(line_number: int, line: str) -> dict:
    fields = line.split("\t")
    if len(fields) != 2:
        raise ValueError(f"line {line_number}: expected exactly two TSV columns, got {len(fields)}")
    raw_headword, raw_definition = fields
    raw_segments = [segment.strip() for segment in raw_headword.split("|") if segment.strip()]
    if not raw_segments:
        raise ValueError(f"line {line_number}: no headword segments")

    lemma = extract_cyrillic_form(raw_segments[0])
    if lemma is None:
        raise ValueError(f"line {line_number}: first segment has no Cyrillic lemma: {raw_segments[0]!r}")

    variants: list[str] = []
    excluded_segments: list[str] = []
    for segment in raw_segments:
        form = extract_cyrillic_form(segment)
        if form is None:
            excluded_segments.append(segment)
            continue
        if form not in variants:
            variants.append(form)

    parts_of_speech = [normalize_text(value) for value in POS_PATTERN.findall(raw_definition)]
    senses = [normalize_text(value) for value in SENSE_PATTERN.findall(raw_definition)]
    flags: list[str] = []
    if not senses:
        flags.append("missing_english_sense")
    # Non-Cyrillic segments are usually legitimate transliterations. Only flag
    # clear multiword English-like fragments as possible scrape navigation.
    if any(ASCII_MULTIWORD.search(segment) for segment in excluded_segments):
        flags.append("possible_scrape_navigation_fragment")

    return {
        "id": f"adyghe-english-wiktionary-v0.1-{line_number:05d}",
        "source_line": line_number,
        "lemma": lemma,
        "variants": variants,
        "part_of_speech": parts_of_speech,
        "english_senses": senses,
        "quality_status": "review_required" if "missing_english_sense" in flags else "accepted",
        "quality_flags": flags,
        "source": "Adyghe-English Wiktionary dictionary.tsv (user-supplied export)",
        "raw_headword_field": raw_headword,
        "excluded_raw_headword_segments": excluded_segments,
        "raw_definition_html": raw_definition,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--audit-json", type=Path, required=True)
    args = parser.parse_args()

    source_hash = sha256(args.source)
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise ValueError("source SHA-256 differs from the pinned Adyghe-English Wiktionary v0.1 export")

    records = [
        parse_row(line_number, line)
        for line_number, line in enumerate(args.source.read_text(encoding="utf-8").splitlines(), start=1)
        if line.strip()
    ]
    duplicate_lemmas = sorted(
        lemma for lemma, count in Counter(record["lemma"] for record in records).items() if count > 1
    )
    pos_counts = Counter(pos for record in records for pos in record["part_of_speech"])
    flag_counts = Counter(flag for record in records for flag in record["quality_flags"])

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    args.output_jsonl.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    audit = {
        "dataset": "adyghe-english-wiktionary-lexicon",
        "version": "v0.1",
        "source_sha256": source_hash,
        "upstream_repository": UPSTREAM_REPOSITORY,
        "upstream_commit": UPSTREAM_COMMIT,
        "upstream_path": UPSTREAM_PATH,
        "upstream_license": UPSTREAM_LICENSE,
        "record_count": len(records),
        "accepted_count": sum(record["quality_status"] == "accepted" for record in records),
        "review_required_count": sum(record["quality_status"] == "review_required" for record in records),
        "part_of_speech_counts": dict(sorted(pos_counts.items())),
        "quality_flag_counts": dict(sorted(flag_counts.items())),
        "duplicate_clean_lemmas": duplicate_lemmas,
        "output_sha256": sha256(args.output_jsonl),
        "cleaning_policy": "Conservatively extract the first/variant leading Cyrillic forms; retain raw source fields and excluded segments for audit. Non-Cyrillic segments are preserved because most are transliterations, but are not included in the Cyrillic lexicon layer. No English senses are rewritten.",
        "training_use": "Use cleaned lemma, variants, POS, and English senses only. This lexicon is not sentence-level parallel data and is not an evaluation reference by itself.",
    }
    args.audit_json.parent.mkdir(parents=True, exist_ok=True)
    args.audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
