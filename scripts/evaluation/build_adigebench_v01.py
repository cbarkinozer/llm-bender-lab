#!/usr/bin/env python3
"""Validate and import the user-provided AdygheBench v0.1 TSV.

The input is intentionally kept outside the training-data workflow.  This tool
creates a model-neutral JSONL evaluation artifact and a machine-readable audit;
it does not create training data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


EXPECTED_ITEMS = 200
RELATED_SOURCE_SHA256 = "70edc807e964cc249282b0a0201eb70be7dcdad401825b761a22d84f0156e810"
DEFAULT_VERSION = "v0.1-candidate"
SOURCE_GROUPS = {
    **{item_id: "crow_story" for item_id in range(97, 99)},
    99: "wind_and_sun_story",
    100: "udhr_article_1",
    **{item_id: "crow_story" for item_id in range(146, 161)},
    **{item_id: "wind_and_sun_story" for item_id in range(161, 176)},
    **{item_id: "udhr_article_1" for item_id in range(176, 181)},
}
MANUAL_REVIEW_TASKS = {"chat_ady_ady", "summary_ady_ady", "contrast_ady_ady"}


def source_contexts(related_source: Path) -> dict[str, dict[str, str]]:
    """Extract the three benchmark passages from the supplied bilingual source."""
    if sha256(related_source) != RELATED_SOURCE_SHA256:
        raise ValueError("related source SHA-256 differs from the pinned adige data.txt artifact")
    pairs = []
    for line in related_source.read_text(encoding="utf-8").splitlines():
        if "\t" in line:
            adyghe, english = line.split("\t", maxsplit=1)
            pairs.append((adyghe.strip(), english.strip()))

    selectors = {
        "crow_story": ("Once upon a time, there was a crow.", "He moved closer to it.", "He picked up those stones"),
        "wind_and_sun_story": ("The breeze and the sun were arguing", "They agreed that whoever", "Then, the wind began", "Then the sun started to shine"),
        "udhr_article_1": ("All human beings are born", "They are endowed with reason"),
    }
    contexts: dict[str, dict[str, str]] = {}
    for group, prefixes in selectors.items():
        selected = [pair for pair in pairs if any(pair[1].startswith(prefix) for prefix in prefixes)]
        if len(selected) != len(prefixes):
            raise ValueError(f"could not recover all {group} passage lines from related source")
        contexts[group] = {
            "adyghe": "\n".join(pair[0] for pair in selected),
            "english": "\n".join(pair[1] for pair in selected),
        }
    return contexts


def normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse(source: Path, contexts: dict[str, dict[str, str]], version: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not re.match(r"^\d{3}\t", line):
            continue
        fields = line.split("\t")
        if len(fields) != 4:
            raise ValueError(f"line {line_number}: expected four TSV fields, found {len(fields)}")
        item_id_text, task, prompt, reference = fields
        item_id = int(item_id_text)
        if not prompt.strip() or not reference.strip():
            raise ValueError(f"line {line_number}: prompt and reference must be non-empty")
        source_group = SOURCE_GROUPS.get(item_id)
        context_language = "english" if item_id <= 100 else "adyghe"
        context = contexts[source_group][context_language] if source_group else None
        rows.append(
            {
                "id": f"adigebench-{version}-{item_id:03d}",
                "source_row_id": item_id_text,
                "task": task,
                "prompt": prompt,
                "references": [reference],
                "source_group": source_group,
                "context": context,
                "scoring": "manual_native_review" if task in MANUAL_REVIEW_TASKS else "exact_match_normalized",
                "native_review_required": task in MANUAL_REVIEW_TASKS or 121 <= item_id <= 145,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--related-source", type=Path, required=True)
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument(
        "--exclude-source-row-ids",
        default="",
        help="comma-separated source row IDs to omit from a curated revision",
    )
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--audit-json", type=Path, required=True)
    args = parser.parse_args()

    contexts = source_contexts(args.related_source)
    all_rows = parse(args.source, contexts, args.version)
    ids = [row["source_row_id"] for row in all_rows]
    expected_ids = [f"{item_id:03d}" for item_id in range(1, EXPECTED_ITEMS + 1)]
    if ids != expected_ids:
        raise ValueError("source IDs must be exactly 001 through 200 in order")
    excluded_ids = {item.strip().zfill(3) for item in args.exclude_source_row_ids.split(",") if item.strip()}
    unknown_exclusions = excluded_ids - set(ids)
    if unknown_exclusions:
        raise ValueError(f"unknown source row IDs in exclusion list: {sorted(unknown_exclusions)}")
    rows = [row for row in all_rows if str(row["source_row_id"]) not in excluded_ids]

    input_groups: defaultdict[str, list[str]] = defaultdict(list)
    prompt_template_groups: defaultdict[str, list[str]] = defaultdict(list)
    for row in rows:
        input_groups[normalized(str(row["context"] or "")) + "\n" + normalized(str(row["prompt"]))].append(str(row["id"]))
        prompt_template_groups[normalized(str(row["prompt"]))].append(str(row["id"]))
    duplicate_inputs = [ids for ids in input_groups.values() if len(ids) > 1]
    duplicate_prompt_templates = [ids for ids in prompt_template_groups.values() if len(ids) > 1]

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    args.output_jsonl.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    audit = {
        "benchmark": "AdygheBench",
        "version": args.version,
        "source": str(args.source),
        "source_sha256": sha256(args.source),
        "related_source": str(args.related_source),
        "related_source_sha256": sha256(args.related_source),
        "item_count": len(rows),
        "excluded_source_row_ids": sorted(excluded_ids),
        "task_counts": dict(sorted(Counter(str(row["task"]) for row in rows).items())),
        "native_review_required_count": sum(bool(row["native_review_required"]) for row in rows),
        "exact_duplicate_inputs": duplicate_inputs,
        "duplicate_prompt_templates": duplicate_prompt_templates,
        "output_jsonl_sha256": sha256(args.output_jsonl),
        "status": "candidate_not_for_final_reporting",
    }
    args.audit_json.parent.mkdir(parents=True, exist_ok=True)
    args.audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
