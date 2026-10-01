#!/usr/bin/env python3
"""Apply completed QA reviews, freeze approved development evaluation and config."""
import csv
import io
import json
import os
from collections import Counter
from copy import deepcopy
from pathlib import Path

import argilla as rg
import yaml
from export_reviews import digest
from import_qa_review import PROPOSALS

ROOT = Path(__file__).resolve().parent
BENCHMARK = ROOT.parent / "exp-007-boundary-benchmark"


def freeze_text(path, text):
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise FileExistsError(f"Frozen artifact differs: {path}; create a new revision rather than overwrite it")
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_json(path, value):
    freeze_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_csv(path, rows, fields):
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    freeze_text(path, handle.getvalue())


def snapshot(dataset):
    return [{"id": record.id, "status": str(record.status), "fields": dict(record.fields),
             "answers": {answer.question_name: answer.value for answer in record.responses}}
            for record in dataset.records]


def main():
    client = rg.Argilla(api_url=os.getenv("ARGILLA_API_URL", "http://127.0.0.1:6900"), api_key=os.getenv("ARGILLA_API_KEY", "argilla.apikey"))
    original_path = ROOT / "data/generalization-reviewed-100.jsonl"
    original = [json.loads(line) for line in original_path.read_text(encoding="utf-8").splitlines()]
    originals = {row["id"]: row for row in original}
    qa_dataset = client.datasets(name="exp-008-post-review-qa", workspace="sft-review")
    qa = snapshot(qa_dataset)
    assert len(qa) == len(PROPOSALS) and {row["id"] for row in qa} == set(PROPOSALS)
    effective = deepcopy(originals)
    for record in qa:
        record_id = record["id"]
        assert record["status"] == "completed", record_id
        assert record["fields"]["prompt_tr"] == originals[record_id]["prompt_tr"]
        assert record["fields"]["previous_reviewed_response"] == originals[record_id]["reviewed_response"]
        assert record["fields"]["proposed_response"] == PROPOSALS[record_id]
        answers = record["answers"]
        decision = answers.get("decision")
        assert decision in {"accept", "rewrite", "reject"}
        reply = answers.get("rewritten_response", "").strip() if decision == "rewrite" else PROPOSALS[record_id] if decision == "accept" else ""
        assert decision == "reject" or reply
        effective[record_id].update(reviewed_response=reply, review_decision=decision,
                                    qa_provenance={"dataset_id": str(qa_dataset.id), "decision": decision, "answers": answers})
    write_json(ROOT / "data/qa-review-export.json", qa)
    accepted = [row for row in effective.values() if row["review_decision"] != "reject"]
    families = sorted({row["capability_family"] for row in accepted})
    prefix = [sorted([row for row in accepted if row["capability_family"] == family], key=lambda row: row["id"])[index]
              for index in range(6) for family in families]
    prefix_ids = {row["id"] for row in prefix}
    ordered = prefix + [row for row in sorted(accepted, key=lambda row: row["id"]) if row["id"] not in prefix_ids]
    training = [{"id": row["id"], "messages": json.dumps([{ "role": "user", "content": row["prompt_tr"]},
                {"role": "assistant", "content": row["reviewed_response"]}], ensure_ascii=False),
                "category": row["capability_family"], "boundary": row["boundary"], "register": row["register"],
                "split": "train", "source": "project-agent-human-reviewed", "quality_status": "accepted", "license": "project-internal-draft"}
                for row in ordered]
    training_path = ROOT / f"data/sft-generalization-final-{len(training)}.csv"
    write_csv(training_path, training, list(training[0]))
    write_json(ROOT / "data/effective-reviews.json", sorted(effective.values(), key=lambda row: row["id"]))

    with (BENCHMARK / "development-v2.csv").open(encoding="utf-8", newline="") as handle:
        benchmark = list(csv.DictReader(handle))
    old_queue = snapshot(client.datasets(name="exp-007-boundary-benchmark-review", workspace="sft-review"))
    changed_queue = snapshot(client.datasets(name="exp-007-boundary-benchmark-v2-changes", workspace="sft-review"))
    changed = {row["id"] for row in changed_queue}
    decisions = {row["id"]: row for row in old_queue if row["id"] not in changed}
    decisions.update({row["id"]: row for row in changed_queue})
    write_json(BENCHMARK / "argilla-review-snapshot.json", {"v1": old_queue, "v2_changes": changed_queue})
    provenance = []
    for row in benchmark:
        record = decisions[row["id"]]
        answers = record["answers"]
        if record["status"] == "completed":
            if answers["decision"] == "reject":
                raise RuntimeError(f"Rejected benchmark must be resolved: {row['id']}")
            if answers["decision"] == "rewrite":
                row["prompt_tr"] = answers.get("rewritten_prompt") or row["prompt_tr"]
                row["pass_condition"] = answers.get("rewritten_pass_condition") or row["pass_condition"]
            method = "explicit-argilla-decision"
        else:
            # The user approved the remaining benchmark conversationally and
            # explicitly authorized the six replacements; no UI status is fabricated.
            method = "conversation-approval: tamamdir bu sekilde iyi sonraki adim nedir"
        row["status"] = "accepted"
        provenance.append({"id": row["id"], "approval_method": method, "argilla_status": record["status"]})
    frozen_benchmark = BENCHMARK / "development-reviewed-v2.csv"
    write_csv(frozen_benchmark, benchmark, list(benchmark[0]))
    write_json(BENCHMARK / "frozen-manifest.json", {"status": "frozen-development", "rows": len(benchmark),
        "sha256": digest(frozen_benchmark), "review_provenance": provenance,
        "limitation": "Development diagnostic informed by earlier failures; not an independent final test."})

    config = yaml.safe_load((ROOT.parent / "exp-006-quality-repair-sft/config.yaml").read_text(encoding="utf-8"))
    config["experiment"] = {"id": "exp-008-generalization-sft", "parent": "exp-006-quality-repair-sft", "status": "ready-for-gpu-preflight",
        "hypothesis": "A standalone balanced human-reviewed rule/exception tranche improves decision behavior on the frozen development benchmark. Data composition and training volume change; broad retention is unproven."}
    config["dataset"] = {"path": str(training_path.relative_to(ROOT)).replace("\\", "/"), "sha256": digest(training_path), "rows": len(training), "split": "train", "builder_artifact": "data/final-manifest.json"}
    config["evaluation"].update(benchmark_path="../exp-007-boundary-benchmark/development-reviewed-v2.csv", benchmark_sha256=digest(frozen_benchmark), benchmark_split="development",
        protocol="evaluation/scoring-rubric.md", selection_policy="Compare the final scheduled adapter with the base; report development results only. Freeze independent evaluation before broader quality claims.")
    config["training"]["starting_artifact"] = "pinned-base-model-not-exp-006-adapter"
    freeze_text(ROOT / "config.yaml", yaml.safe_dump(config, sort_keys=False, allow_unicode=True))
    manifest = {"status": "frozen-reviewed", "rows": len(training), "families": dict(Counter(row["category"] for row in training)),
        "qa_reviews_applied": len(qa), "qa_decisions": dict(Counter(row["answers"]["decision"] for row in qa)),
        "initial_review_decisions": dict(Counter(row["review_decision"] for row in original)),
        "recipe": "Standalone 100-example diagnostic pilot from pinned base; exp-006 training hyperparameters retained. No old-core append.",
        "tiny_overfit_order": "First 30 rows contain six examples per family.",
        "artifacts": {path.name: digest(path) for path in (original_path, ROOT / "data/qa-review-export.json", ROOT / "data/effective-reviews.json", training_path)},
        "benchmark_sha256": digest(frozen_benchmark)}
    write_json(ROOT / "data/final-manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
