"""Read-only verification of frozen prompt artifacts, with a separate audit output."""
import csv
import hashlib
import io
import json
import re
from collections import Counter
from difflib import SequenceMatcher

from build_selection import HERE, ROOT, SOURCES, content_only, normalize, save, encode_json


def main():
    manifest = json.loads((HERE / "data/selection-manifest.json").read_text(encoding="utf-8"))
    for name, info in manifest["artifacts"].items():
        raw = (HERE / "data" / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == info["sha256"], name
    rows = [json.loads(line) for line in (HERE / "data/prompts-100.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == len({r["id"] for r in rows}) == 100
    assert Counter(r["split"] for r in rows) == {"train": 80, "validation": 20}
    assert len({normalize(r["prompt_tr"]) for r in rows}) == 100
    for category in manifest["category_counts"]:
        assert Counter(r["split"] for r in rows if r["category"] == category) == {"train": 8, "validation": 2}
    for split, count in [("train", 80), ("validation", 20)]:
        subset = [json.loads(line) for line in (HERE / f"data/{split}-prompts-{count}.jsonl").read_text(encoding="utf-8").splitlines()]
        assert subset == [r for r in rows if r["split"] == split]
    pools = {}
    for relative, info in manifest["inputs"].items():
        raw = (ROOT / relative).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == info["sha256_bytes"]
        pools[relative] = {r["id"]: r for r in csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))}
    for row in rows:
        source = pools[row["source_path"]][row["source_id"]]
        messages = json.loads(source["messages"])
        assert row["prompt_tr"] == messages[0]["content"]
        assert row["messages"] == [{"role": "user", "content": row["prompt_tr"]}]
        assert row["answer_status"] == "not-generated"
    train = [r for r in rows if r["split"] == "train"]
    validation = [r for r in rows if r["split"] == "validation"]
    assert not ({r["scenario_group_id"] for r in train} & {r["scenario_group_id"] for r in validation})
    assert not ({(r["source_path"], r["source_id"]) for r in train} & {(r["source_path"], r["source_id"]) for r in validation})
    closest = []
    for val in validation:
        scores = sorted([{
            "validation_id": val["id"], "train_id": t["id"],
            "similarity": round(SequenceMatcher(None, content_only(val["prompt_tr"]), content_only(t["prompt_tr"]), autojunk=False).ratio(), 4)
        } for t in train], key=lambda r: r["similarity"], reverse=True)
        closest.extend(scores[:3])
    benchmark_paths = [
        ROOT / "exp-002-communication-policy-benchmark/development.csv",
        ROOT / "exp-002-communication-policy-benchmark/test.csv",
        ROOT / "exp-002-communication-policy-benchmark/test-v2.1.csv",
        ROOT / "exp-005-targeted-policy-sft/evaluation/final-holdout-v1.csv",
        ROOT / "exp-006-quality-repair-sft/evaluation/final-holdout-v2.csv",
        ROOT / "exp-007-boundary-benchmark/development-reviewed-v2.csv",
    ]
    benchmarks = []
    benchmark_inputs = {}
    for path in benchmark_paths:
        raw = path.read_bytes()
        parsed = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
        benchmark_inputs[str(path.relative_to(ROOT)).replace("\\", "/")] = {"rows": len(parsed), "sha256_bytes": hashlib.sha256(raw).hexdigest()}
        for b in parsed:
            if b.get("prompt_tr"):
                benchmarks.append((str(path.relative_to(ROOT)), b["id"], b["prompt_tr"]))
    exact, near = [], []
    for r in rows:
        for path, bid, prompt in benchmarks:
            a, b = normalize(r["prompt_tr"]), normalize(prompt)
            score = SequenceMatcher(None, a, b, autojunk=False).ratio()
            if a == b:
                exact.append({"selection_id": r["id"], "benchmark_path": path, "benchmark_id": bid})
            elif score >= .78:
                near.append({"selection_id": r["id"], "benchmark_path": path, "benchmark_id": bid, "similarity": round(score, 4)})
    assert not exact, exact
    report = {
        "structural_and_hash_checks": "passed", "source_prompt_binding": "passed",
        "train_rows": 80, "validation_rows": 20, "cross_split_pairs_checked": len(train)*len(validation),
        "cross_split_exact_prompt_overlap": 0, "cross_split_group_overlap": 0,
        "cross_split_source_identity_overlap": 0, "historical_targets_copied": 0,
        "benchmark_inputs": benchmark_inputs, "benchmark_rows_scanned": len(benchmarks),
        "benchmark_exact_matches": exact, "benchmark_near_threshold": .78, "benchmark_near_matches": near,
        "closest_train_pairs_per_validation": closest,
        "scope": "New base-start phase; no novelty claim against historical adapters. No unseen evaluation outputs read.",
        "limitation": "Lexical checks cannot prove semantic independence. Manual review is separately documented."
    }
    save(HERE / "data/audit-report.json", encode_json(report))
    print(json.dumps({"checks": "passed", "benchmark_rows": len(benchmarks), "benchmark_near_matches": near,
                      "closest_cross_split": sorted(closest, key=lambda r: r["similarity"], reverse=True)[:12]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
