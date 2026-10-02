#!/usr/bin/env python3
"""Import anonymized development results with item anchors and compact review."""
import csv
import json
import os
from pathlib import Path

import argilla as rg

ROOT = Path(__file__).resolve().parent


def main():
    with (ROOT / "results/blind-review/blind-review.csv").open(encoding="utf-8", newline="") as handle:
        pairs = list(csv.DictReader(handle))
    with (ROOT.parent / "exp-007-boundary-benchmark/development-reviewed-v2.csv").open(encoding="utf-8", newline="") as handle:
        anchors = {row["id"]: row for row in csv.DictReader(handle)}
    assert len(pairs) == len(anchors) == 50
    assert {row["id"] for row in pairs} == set(anchors)
    client = rg.Argilla(api_url=os.getenv("ARGILLA_API_URL", "http://127.0.0.1:6900"), api_key=os.getenv("ARGILLA_API_KEY", "argilla.apikey"))
    name = "exp-008-development-v2-blind-v1"
    existing = client.datasets(name=name, workspace="sft-review")
    if existing is not None:
        raise RuntimeError("Existing blind reviews will not be replaced")
    failures = ["unnecessary_clarification", "unsupported_fact_or_cause", "lost_qualification", "invented_self_state",
                "turkish_or_meaning_error", "contradiction", "repetition", "incomplete_answer"]
    settings = rg.Settings(
        guidelines="Blind development comparison: identities are randomized. Judge task completion and correctness before style, using each item's scoring anchor. Equivalent wording is valid. Select A/B/tie; mark task completion for each. Select only applicable failures. Shortness alone is not success. This is a development benchmark, not independent final evidence.",
        fields=[rg.TextField(name=field, use_markdown=False) for field in ("prompt_tr", "output_a", "output_b", "expected_mode", "pass_condition")],
        questions=[rg.LabelQuestion(name="pairwise_preference", labels=["A", "B", "tie"], required=True),
                   rg.LabelQuestion(name="task_completion_a", labels=["pass", "fail"], required=True),
                   rg.LabelQuestion(name="task_completion_b", labels=["pass", "fail"], required=True),
                   rg.MultiLabelQuestion(name="policy_failures_a", labels=failures, required=False),
                   rg.MultiLabelQuestion(name="policy_failures_b", labels=failures, required=False),
                   rg.TextQuestion(name="review_notes", required=False)],
        metadata=[rg.TermsMetadataProperty(name="category", options=sorted({row["category"] for row in pairs}))])
    dataset = rg.Dataset(name=name, workspace="sft-review", settings=settings, client=client).create()
    dataset.records.log([rg.Record(id=row["id"], fields={
        **{field: row[field] for field in ("prompt_tr", "output_a", "output_b")},
        **{field: anchors[row["id"]][field] for field in ("expected_mode", "pass_condition")}},
        metadata={"category": row["category"]}) for row in pairs])
    print(json.dumps({"name": name, "records": len(list(dataset.records)),
                      "url": f"http://127.0.0.1:6900/dataset/{dataset.id}/annotation-mode"}, indent=2))


if __name__ == "__main__":
    main()
