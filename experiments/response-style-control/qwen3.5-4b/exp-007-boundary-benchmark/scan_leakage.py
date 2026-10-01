#!/usr/bin/env python3
"""Compare benchmark prompts with historical and current training pools."""
import argparse
import csv
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL = ROOT.parent
POOLS = [MODEL / "exp-001-sft-dataset/reviewed-v3/accepted-reviewed.csv",
         MODEL / "exp-006-quality-repair-sft/data/sft-clean-v4-quality-repair-958.csv",
         MODEL / "exp-008-generalization-sft/data/sft-generalization-reviewed-100.csv"]


def normalize(value):
    return re.sub(r"[^\w]+", " ", unicodedata.normalize("NFKC", value).casefold()).strip()


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=ROOT / "development-v2.csv")
    args = parser.parse_args()
    pool = []
    for path in POOLS:
        for row in read(path):
            user = next(message["content"] for message in json.loads(row["messages"]) if message["role"] == "user")
            pool.append({"pool": str(path.relative_to(MODEL)), "id": row["id"], "prompt": user, "normalized": normalize(user)})
    benchmark = read(args.benchmark)
    assert len(benchmark) == 50 and len({row["id"] for row in benchmark}) == 50
    assert len({normalize(row["prompt_tr"]) for row in benchmark}) == 50
    results = []
    for item in benchmark:
        value = normalize(item["prompt_tr"])
        matches = []
        for candidate in pool:
            ratio = SequenceMatcher(None, value, candidate["normalized"]).ratio()
            matches.append({"id": candidate["id"], "pool": candidate["pool"], "prompt": candidate["prompt"], "similarity": round(ratio, 4), "exact": value == candidate["normalized"]})
        matches.sort(key=lambda match: match["similarity"], reverse=True)
        results.append({"id": item["id"], "prompt": item["prompt_tr"], "closest": matches[:3]})
    report = {"benchmark_path": args.benchmark.name, "benchmark_rows": len(benchmark), "training_rows_scanned": len(pool),
              "unique_training_prompts": len({row["normalized"] for row in pool}),
              "exact_matches": [item for item in results if item["closest"][0]["exact"]],
              "near_threshold": 0.82, "near_matches": [item for item in results if item["closest"][0]["similarity"] >= 0.82],
              "closest_matches": results, "limitation": "Lexical ranking supplies audit candidates; conceptual overlap needs manual examination."}
    (ROOT / f"leakage-scan-{args.benchmark.stem}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Benchmarks={len(benchmark)} training_rows={len(pool)} unique_prompts={report['unique_training_prompts']} exact={len(report['exact_matches'])} near={len(report['near_matches'])}")
    for item in results:
        match = item["closest"][0]
        print(f"{item['id']} | {item['prompt']}\n  {match['id']} ({match['similarity']}): {match['prompt']}")


if __name__ == "__main__":
    main()
