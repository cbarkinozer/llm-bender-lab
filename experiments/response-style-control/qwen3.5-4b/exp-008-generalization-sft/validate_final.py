#!/usr/bin/env python3
"""Validate frozen effective targets, QA binding, benchmark provenance and hashes."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import yaml
from validate_candidates import normalized

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data/final-manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["artifacts"].items():
        assert digest(ROOT / "data" / name) == expected, name
    train_path = ROOT / config["dataset"]["path"]
    benchmark_path = ROOT / config["evaluation"]["benchmark_path"]
    train = read_csv(train_path)
    benchmark = read_csv(benchmark_path)
    assert digest(train_path) == config["dataset"]["sha256"]
    assert digest(benchmark_path) == config["evaluation"]["benchmark_sha256"]
    assert len(train) == config["dataset"]["rows"] == 100
    assert len(benchmark) == 50
    assert len({row["id"] for row in train}) == 100
    assert len({row["id"] for row in benchmark}) == 50
    assert Counter(row["category"] for row in train) == {family: 20 for family in manifest["families"]}
    assert Counter(row["category"] for row in train[:30]) == {family: 6 for family in manifest["families"]}
    effective = {row["id"]: row for row in json.loads((ROOT / "data/effective-reviews.json").read_text(encoding="utf-8"))}
    original = {row["id"]: row for row in (json.loads(line) for line in (ROOT / "data/generalization-reviewed-100.jsonl").read_text(encoding="utf-8").splitlines())}
    qa = json.loads((ROOT / "data/qa-review-export.json").read_text(encoding="utf-8"))
    qa_ids = {row["id"] for row in qa}
    for record in qa:
        assert record["status"] == "completed"
        assert effective[record["id"]]["reviewed_response"] == record["answers"]["rewritten_response"].strip()
    prompts = []
    for row in train:
        review = effective[row["id"]]
        if row["id"] not in qa_ids:
            assert review == original[row["id"]]
        messages = json.loads(row["messages"])
        assert messages == [{"role": "user", "content": review["prompt_tr"]}, {"role": "assistant", "content": review["reviewed_response"]}]
        assert all(message["content"].strip() and "\ufffd" not in message["content"] for message in messages)
        assert row["quality_status"] == "accepted" and row["split"] == "train"
        prompts.append(normalized(messages[0]["content"]))
    assert len(set(prompts)) == 100
    assert not set(prompts) & {normalized(row["prompt_tr"]) for row in benchmark}
    benchmark_manifest = json.loads((benchmark_path.parent / "frozen-manifest.json").read_text(encoding="utf-8"))
    assert benchmark_manifest["sha256"] == digest(benchmark_path)
    assert {row["id"] for row in benchmark_manifest["review_provenance"]} == {row["id"] for row in benchmark}
    assert all(row["status"] == "accepted" and row["pass_condition"].strip() for row in benchmark)
    report = {"status": "passed", "training_rows": 100, "benchmark_rows": 50, "qa_corrections_applied": 11,
              "unmodified_initial_reviews": 89, "exact_train_benchmark_overlaps": 0,
              "scope": "Structural, provenance and artifact checks; six scenario overlaps resolved in the documented manual audit. Token lengths, masking and GPU behavior require GPU preflight."}
    with (ROOT / "evaluation/final-preparation-report.json").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
