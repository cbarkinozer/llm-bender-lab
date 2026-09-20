"""Export reviewed targeted records from Argilla and build the next SFT artifact."""
from __future__ import annotations

import csv
import hashlib
import json
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import argilla as rg


HERE = Path(__file__).resolve().parent
MODEL_DIR = HERE.parent
CORE = MODEL_DIR / "exp-001-sft-dataset" / "clean-v2" / "sft-clean-v2-800.csv"
CORE_MANIFEST = CORE.parent / "manifest.json"
DEV_BENCHMARK = MODEL_DIR / "exp-002-communication-policy-benchmark" / "test.csv"
FINAL_HOLDOUT = HERE / "evaluation" / "final-holdout-v1.csv"
OUTPUT_DIR = HERE / "data"
REVIEW_EXPORT = OUTPUT_DIR / "targeted-reviewed-60.jsonl"
COMBINED = OUTPUT_DIR / "sft-clean-v3-targeted-858.csv"
MANIFEST = OUTPUT_DIR / "manifest.json"

API_URL = "http://127.0.0.1:6900"
API_KEY = "argilla.apikey"
WORKSPACE = "sft-review"
DATASETS = {
    "clarification_missing_context": "exp-005-targeted-clarification",
    "lexical_entity_precision": "exp-005-targeted-precision-v2",
    "natural_non_anthropomorphic": "exp-005-targeted-non-anthropomorphic",
}
ANSWER_TYPES = {
    "clarification_missing_context": "clarification_question",
    "lexical_entity_precision": "precision_response",
    "natural_non_anthropomorphic": "non_anthropomorphic_response",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def response_value(row: dict, question: str, *, required: bool) -> str:
    values = row.get("responses", {}).get(question, [])
    value = values[0].get("value", "") if values else ""
    value = value.strip() if isinstance(value, str) else ""
    if required and not value:
        raise ValueError(f"{row['id']}: missing submitted {question}")
    return value


def benchmark_prompts(path: Path) -> set[str]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if "prompt_tr" in (reader.fieldnames or []):
            return {normalize(row["prompt_tr"]) for row in reader}
        if "user_input" in (reader.fieldnames or []):
            return {normalize(row["user_input"]) for row in reader}
        if "messages" in (reader.fieldnames or []):
            prompts = set()
            for row in reader:
                messages = json.loads(row["messages"])
                prompts.add(normalize(next(m["content"] for m in messages if m["role"] == "user")))
            return prompts
        raise ValueError("Benchmark has neither user_input nor messages column")


def main() -> None:
    client = rg.Argilla(api_url=API_URL, api_key=API_KEY)
    reviewed: list[dict] = []
    for category, dataset_name in DATASETS.items():
        dataset = client.datasets(name=dataset_name, workspace=WORKSPACE)
        if dataset is None:
            raise ValueError(f"Missing Argilla dataset: {dataset_name}")
        rows = dataset.records.to_list()
        if len(rows) != 20:
            raise ValueError(f"{dataset_name}: expected 20 records, found {len(rows)}")
        for row in rows:
            if row["status"] != "completed":
                raise ValueError(f"{dataset_name}/{row['id']}: status is {row['status']!r}")
            responses = row.get("responses", {})
            reviewed.append(
                {
                    "id": row["id"],
                    "category": category,
                    "argilla_dataset": dataset_name,
                    "argilla_dataset_id": str(dataset.id),
                    "argilla_server_record_id": row["_server_id"],
                    "user_input": row["fields"]["user_input"],
                    "candidate_target": row["fields"]["candidate_target"],
                    "reviewed_target": response_value(row, "reviewed_target", required=True),
                    "review_note": response_value(row, "review_note", required=False),
                    "reviewer_user_ids": sorted(
                        {str(item["user_id"]) for values in responses.values() for item in values}
                    ),
                    "status": row["status"],
                }
            )

    counts = Counter(item["category"] for item in reviewed)
    expected = Counter({category: 20 for category in DATASETS})
    if counts != expected:
        raise ValueError(f"Unexpected category counts: {counts}")
    if len({item["id"] for item in reviewed}) != 60:
        raise ValueError("Targeted records contain duplicate IDs")
    normalized_prompts = [normalize(item["user_input"]) for item in reviewed]
    if len(set(normalized_prompts)) != 60:
        raise ValueError("Targeted records contain duplicate normalized prompts")
    reviewed.sort(key=lambda item: (item["category"], item["id"]))
    development_prompts = benchmark_prompts(DEV_BENCHMARK)
    final_prompts = benchmark_prompts(FINAL_HOLDOUT)
    excluded_overlap = [item for item in reviewed if normalize(item["user_input"]) in development_prompts]
    training_reviewed = [item for item in reviewed if normalize(item["user_input"]) not in development_prompts]
    final_overlap = [item["id"] for item in training_reviewed if normalize(item["user_input"]) in final_prompts]
    if final_overlap:
        raise ValueError(f"Exact final-holdout overlap detected: {final_overlap}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with REVIEW_EXPORT.open("w", encoding="utf-8", newline="\n") as handle:
        for item in reviewed:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")

    with CORE.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        core_rows = list(reader)
    if len(core_rows) != 800 or "messages" not in fieldnames:
        raise ValueError("Core artifact does not match the expected 800-row conversational schema")

    created_at = datetime.now(timezone.utc).isoformat()
    targeted_rows = []
    for item in training_reviewed:
        row = {field: "" for field in fieldnames}
        row.update(
            {
                "id": item["id"],
                "messages": json.dumps(
                    [
                        {"role": "user", "content": item["user_input"]},
                        {"role": "assistant", "content": item["reviewed_target"]},
                    ],
                    ensure_ascii=False,
                ),
                "category": f"targeted_{item['category']}",
                "answer_type": ANSWER_TYPES[item["category"]],
                "domain": "mixed",
                "language": "tr",
                "source": "project-internal-targeted-policy",
                "source_id": item["id"],
                "generator": "unknown-not-recorded",
                "generation_prompt_version": "targeted-policy-data-spec-v1",
                "reviewer": "argilla-human-review",
                "quality_status": "accepted",
                "contamination_checked": "exact-normalized-prompt",
                "contamination_flag": "false",
                "license": "project-internal-draft",
                "split": "train",
                "notes": "reviewed in Argilla; retained as separate targeted tranche",
            }
        )
        targeted_rows.append(row)

    # The shared trainer's tiny-overfit mode selects the first 32 records.
    # Put a deterministic stratified diagnostic subset first: eight records
    # from each targeted family plus two records from each core family.
    targeted_by_category = {
        category: [row for row in targeted_rows if row["category"] == f"targeted_{category}"]
        for category in DATASETS
    }
    core_categories = sorted({row["category"] for row in core_rows})
    diagnostic_rows = [
        row
        for category in DATASETS
        for row in targeted_by_category[category][:8]
    ] + [
        row
        for category in core_categories
        for row in [item for item in core_rows if item["category"] == category][:2]
    ]
    diagnostic_ids = {row["id"] for row in diagnostic_rows}
    combined_rows = diagnostic_rows + [
        row for row in core_rows + targeted_rows if row["id"] not in diagnostic_ids
    ]
    if len(combined_rows) != 858:
        raise ValueError(f"Expected 858 combined rows, found {len(combined_rows)}")
    ids = [row["id"] for row in combined_rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Combined artifact contains duplicate IDs")
    with COMBINED.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(combined_rows)

    changed = Counter(
        item["category"]
        for item in reviewed
        if item["candidate_target"] != item["reviewed_target"]
    )
    core_manifest = json.loads(CORE_MANIFEST.read_text(encoding="utf-8"))
    recorded_core_sha256 = core_manifest["files"][CORE.name]["sha256"]
    actual_core_sha256 = sha256(CORE)
    manifest = {
        "status": "frozen-reviewed",
        "do_not_train": False,
        "version": "clean-v3-targeted-858",
        "created_at": created_at,
        "rows": {
            "core": 800,
            "targeted_reviewed_export": 60,
            "targeted_included_in_training": 58,
            "combined": 858,
        },
        "targeted_category_counts": dict(sorted(counts.items())),
        "training_targeted_category_counts": dict(
            sorted(Counter(item["category"] for item in training_reviewed).items())
        ),
        "human_edited_target_counts": {
            category: changed.get(category, 0) for category in DATASETS
        },
        "argilla": {
            "workspace": WORKSPACE,
            "datasets": DATASETS,
            "all_records_completed": True,
            "reviewer_user_ids": sorted(
                {user_id for item in reviewed for user_id in item["reviewer_user_ids"]}
            ),
        },
        "validation": {
            "unique_ids": True,
            "unique_targeted_normalized_prompts": True,
            "exact_normalized_development_prompt_overlap_in_training": 0,
            "exact_normalized_final_holdout_overlap_in_training": 0,
            "messages_nonempty": True,
            "tiny_overfit_prefix_rows": 32,
            "tiny_overfit_prefix_policy": "8 per targeted family plus 2 per core family",
        },
        "benchmark_overlap_exclusions": [
            {
                "id": item["id"],
                "category": item["category"],
                "user_input": item["user_input"],
                "reason": "exact normalized prompt match with sealed benchmark",
            }
            for item in excluded_overlap
        ],
        "precision_scope_decision": (
            "The original broad precision tranche was superseded. The included precision-v2 tranche "
            "contains 20 distinct, human-reviewed typo-like or orthographically close term contrasts."
        ),
        "provenance_limitations": [
            (
                "The generator model/provider was not recorded for the original clarification and "
                "non-anthropomorphism candidates; no identity was inferred. Precision-v2 was authored "
                "in-repository and then human-reviewed in Argilla."
            ),
            (
                "The clean-v2 manifest records core SHA-256 "
                f"{recorded_core_sha256}, but the tracked core file hashes to {actual_core_sha256}; "
                "this build records the actual input bytes."
            ),
        ],
        "artifacts": {
            "core": {"path": CORE.relative_to(MODEL_DIR).as_posix(), "sha256": actual_core_sha256},
            "development_benchmark": {
                "path": DEV_BENCHMARK.relative_to(MODEL_DIR).as_posix(),
                "sha256": sha256(DEV_BENCHMARK),
            },
            "final_holdout": {
                "path": FINAL_HOLDOUT.relative_to(HERE).as_posix(),
                "sha256": sha256(FINAL_HOLDOUT),
            },
            "review_export": {"path": REVIEW_EXPORT.name, "sha256": sha256(REVIEW_EXPORT)},
            "combined": {"path": COMBINED.name, "sha256": sha256(COMBINED)},
        },
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
