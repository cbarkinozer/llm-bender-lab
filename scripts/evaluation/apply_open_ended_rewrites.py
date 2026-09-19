#!/usr/bin/env python3
"""Apply a human rewrite export to the clean open-ended SFT category."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rewrites", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/clean-v2"))
    args = parser.parse_args()
    out_dir = args.output_dir
    target = out_dir / "open_ended_counterexample.csv"
    with args.rewrites.open(encoding="utf-8-sig", newline="") as handle:
        rewrite_rows = list(csv.DictReader(handle))
    required = {"id", "status", "assistant_content"}
    if not rewrite_rows or not required.issubset(rewrite_rows[0]):
        raise ValueError(f"Rewrite file must contain {sorted(required)}")
    mapping = {row["id"]: row for row in rewrite_rows}
    if len(mapping) != len(rewrite_rows):
        raise ValueError("Rewrite IDs are not unique")

    with target.open(encoding="utf-8-sig", newline="") as handle:
        base_rows = list(csv.DictReader(handle))
    base_ids = {row["id"] for row in base_rows}
    if base_ids != set(mapping):
        raise ValueError(f"ID mismatch: base={len(base_ids)}, rewrites={len(mapping)}")

    rewritten_ids = []
    unchanged_ids = []
    for row in base_rows:
        review = mapping[row["id"]]
        status = review["status"].strip().lower()
        if status == "rewritten":
            content = review["assistant_content"].strip()
            if not content:
                raise ValueError(f"Empty assistant_content for rewritten row {row['id']}")
            messages = json.loads(row["messages"])
            messages[1]["content"] = content
            row["messages"] = json.dumps(messages, ensure_ascii=False)
            row["notes"] = (row.get("notes", "").rstrip(" | ") + " | human rewrite import").strip(" |")
            rewritten_ids.append(row["id"])
        elif status == "unchanged":
            unchanged_ids.append(row["id"])
        else:
            raise ValueError(f"Unsupported status {status!r} for {row['id']}")

    # Preserve the exact human export beside the resulting artifact.
    archived_input = out_dir / "open_ended_counterexample_rewrites.csv"
    shutil.copyfile(args.rewrites, archived_input)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(base_rows[0]))
        writer.writeheader(); writer.writerows(base_rows)

    combined = out_dir / "sft-clean-v2-800.csv"
    category_files = ["bare_qa_span.csv", "terse_summary.csv", "numeric_entity_precision_qa.csv", "open_ended_counterexample.csv"]
    all_rows = []
    for filename in category_files:
        with (out_dir / filename).open(encoding="utf-8-sig", newline="") as handle:
            all_rows.extend(csv.DictReader(handle))
    with combined.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader(); writer.writerows(all_rows)

    main_manifest = out_dir / "manifest.json"
    if main_manifest.exists():
        manifest_data = json.loads(main_manifest.read_text(encoding="utf-8"))
        manifest_data.setdefault("files", {}).setdefault("sft-clean-v2-800.csv", {})["sha256"] = sha256(combined)
        manifest_data["files"]["sft-clean-v2-800.csv"]["rows"] = len(all_rows)
        main_manifest.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = {
        "version": "clean-sft-v2-open-ended-human-rewrites",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_rewrite_file_sha256": sha256(args.rewrites),
        "rewritten_rows": len(rewritten_ids),
        "unchanged_rows": len(unchanged_ids),
        "unchanged_ids": unchanged_ids,
        "output_sha256": sha256(target),
        "combined_sha256": sha256(combined),
    }
    (out_dir / "open_ended_counterexample.rewrite-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
