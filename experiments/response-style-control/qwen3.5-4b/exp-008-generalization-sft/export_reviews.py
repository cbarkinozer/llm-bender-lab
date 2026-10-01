#!/usr/bin/env python3
"""Export completed Argilla reviews and build an independently reviewed tranche."""
import csv
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

import argilla as rg

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def digest(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    with (DATA / "candidates-v1.csv").open(encoding="utf-8", newline="") as handle:
        candidates = list(csv.DictReader(handle))
    client = rg.Argilla(api_url=os.getenv("ARGILLA_API_URL", "http://127.0.0.1:6900"),
                        api_key=os.getenv("ARGILLA_API_KEY", "argilla.apikey"))
    reviewed = []
    datasets = []
    for family in sorted({row["capability_family"] for row in candidates}):
        dataset = client.datasets(name=f"exp-008-{family.replace('_', '-')}", workspace="sft-review")
        if dataset is None:
            raise RuntimeError(f"Missing dataset: {family}")
        expected = {row["id"]: row for row in candidates if row["capability_family"] == family}
        records = list(dataset.records)
        if len(records) != len(expected) or {record.id for record in records} != set(expected):
            raise ValueError(f"Record coverage mismatch: {family}")
        for record in records:
            if str(record.status) != "completed":
                raise RuntimeError(f"Incomplete review: {record.id}")
            source = expected[record.id]
            for field in ("prompt_tr", "proposed_response", "boundary", "register"):
                if record.fields[field] != source[field]:
                    raise ValueError(f"Source changed in Argilla: {record.id}/{field}")
            answers = {response.question_name: response.value for response in (record.responses or [])}
            decision = answers.get("decision")
            replacement = (answers.get("rewritten_response") or "").strip()
            if decision not in {"accept", "rewrite", "reject"} or (decision == "rewrite" and not replacement):
                raise ValueError(f"Invalid review: {record.id}")
            reviewed.append({**source, "review_decision": decision,
                             "reviewed_response": replacement if decision == "rewrite" else source["proposed_response"] if decision == "accept" else "",
                             "failure_tags": answers.get("failure_tags") or [],
                             "review_notes": answers.get("review_notes") or "",
                             "argilla_dataset_id": str(dataset.id), "review_status": "completed"})
        datasets.append({"name": dataset.name, "id": str(dataset.id), "records": len(records)})
    reviewed.sort(key=lambda row: row["id"])
    output = DATA / "generalization-reviewed-100.jsonl"
    output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in reviewed), encoding="utf-8")
    accepted = [row for row in reviewed if row["review_decision"] != "reject"]
    training = DATA / f"sft-generalization-reviewed-{len(accepted)}.csv"
    with training.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "messages", "category", "boundary", "register", "split", "source", "quality_status", "license"])
        writer.writeheader()
        for row in accepted:
            writer.writerow({"id": row["id"], "messages": json.dumps([
                {"role": "user", "content": row["prompt_tr"]},
                {"role": "assistant", "content": row["reviewed_response"]}], ensure_ascii=False),
                "category": row["capability_family"], "boundary": row["boundary"], "register": row["register"],
                "split": "train", "source": "project-agent-human-reviewed", "quality_status": "accepted", "license": "project-internal-draft"})
    manifest = {"status": "human-reviewed; post-review-QA-required", "reviewed": len(reviewed), "accepted": len(accepted),
                "rejected": len(reviewed) - len(accepted), "decisions": dict(Counter(row["review_decision"] for row in reviewed)),
                "accepted_families": dict(Counter(row["capability_family"] for row in accepted)), "datasets": datasets,
                "artifacts": {path.name: digest(path) for path in (DATA / "candidates-v1.csv", output, training)},
                "mixture": "Standalone reviewed tranche; not appended to exp-006. Final training recipe remains pending."}
    (DATA / "review-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
