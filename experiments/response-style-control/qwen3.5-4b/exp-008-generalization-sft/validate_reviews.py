#!/usr/bin/env python3
"""Check durable reviews and expose issues without modifying human annotations."""
import json
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from export_reviews import digest
from validate_candidates import KNOWN, normalized, prompt, rows

ROOT = Path(__file__).resolve().parent
ISSUES = {
    "gen-001": "Guarantees reception delivery and a specific failed-delivery procedure without knowing the carrier.",
    "gen-003": "Overgeneralizes frost killing most balcony plants and their roots overnight without species or temperature.",
    "gen-007": "Adds unsupported advice that replacing the complete zipper is more durable than replacing its slider.",
    "gen-013": "Guarantees one-hour paint state, damage, and safe closure after four hours without product conditions.",
    "gen-033": "Assigns an unsupported probability to bank involvement in a payment-page failure.",
    "gen-044": "Treats payment as a universal prerequisite for ticket issuance; reservation rules are not provided.",
    "gen-058": "Invents a registration entitlement and concludes registration is incomplete from missing confirmation.",
    "gen-062": "Claims a prior failure to notice and a reason for silence despite having no prior conversation context.",
    "gen-067": "Assumes the user worked on the task for a long time.",
    "gen-095": "Only Zeynep's objection was verified; other participants' acceptance remains unknown.",
    "gen-097": "Absence of a no-errors statement does not imply the report says nothing about errors.",
}


def main():
    data = ROOT / "data"
    candidates = {row["id"]: row for row in rows(data / "candidates-v1.csv")}
    reviewed = [json.loads(line) for line in (data / "generalization-reviewed-100.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(reviewed) == 100 and len({row["id"] for row in reviewed}) == 100
    assert {row["id"] for row in reviewed} == set(candidates)
    accepted = [row for row in reviewed if row["review_decision"] != "reject"]
    for row in reviewed:
        assert all(row[field] == candidates[row["id"]][field] for field in candidates[row["id"]])
        assert row["review_decision"] in {"accept", "rewrite", "reject"}
        assert bool(row["reviewed_response"].strip()) == (row["review_decision"] != "reject")
        assert "\ufffd" not in row["reviewed_response"]
    manifest = json.loads((data / "review-manifest.json").read_text(encoding="utf-8"))
    assert all(digest(data / name) == expected for name, expected in manifest["artifacts"].items())
    training = rows(data / f"sft-generalization-reviewed-{len(accepted)}.csv")
    assert len(training) == len(accepted)
    for train, review in zip(training, accepted, strict=True):
        assert train["id"] == review["id"]
        messages = json.loads(train["messages"])
        assert messages == [{"role": "user", "content": review["prompt_tr"]}, {"role": "assistant", "content": review["reviewed_response"]}]
    known = [(path.name, row["id"], normalized(prompt(row))) for path in KNOWN for row in rows(path)]
    overlaps = [(row["id"], filename, other_id) for row in accepted for filename, other_id, other in known if normalized(row["prompt_tr"]) == other]
    assert not overlaps, overlaps
    near = []
    for row in accepted:
        current = normalized(row["prompt_tr"])
        for filename, other_id, other in known:
            similarity = SequenceMatcher(None, current, other).ratio()
            if similarity >= 0.82:
                near.append({"id": row["id"], "pool": filename, "other_id": other_id, "similarity": round(similarity, 4)})
    findings = [{"id": row["id"], "issue": ISSUES[row["id"]], "prompt": row["prompt_tr"], "reviewed_response": row["reviewed_response"]} for row in accepted if row["id"] in ISSUES]
    report = {"status": "blocked-on-semantic-QA" if findings or near else "structural-QA-passed",
              "reviewed": len(reviewed), "accepted": len(accepted), "decisions": dict(Counter(row["review_decision"] for row in reviewed)),
              "exact_overlaps": overlaps, "near_overlap_threshold": 0.82, "near_overlap_candidates": near,
              "semantic_findings": findings, "human_review_preserved": True,
              "limitation": "Lexical checks do not establish conceptual independence. Semantic findings require correction before training."}
    evaluation = ROOT / "evaluation"
    evaluation.mkdir(exist_ok=True)
    (evaluation / "reviewed-quality-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "semantic_findings"}, ensure_ascii=False, indent=2))
    print(f"Semantic findings requiring correction: {len(findings)}")


if __name__ == "__main__":
    main()
