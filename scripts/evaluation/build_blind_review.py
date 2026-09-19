#!/usr/bin/env python3
"""Create an anonymized paired review set from base/candidate outputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--base-output", type=Path, required=True)
    parser.add_argument("--candidate-output", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=3407)
    args = parser.parse_args()

    rows = list(csv.DictReader(args.benchmark.open(encoding="utf-8", newline="")))
    base = [json.loads(line) for line in args.base_output.read_text(encoding="utf-8").splitlines() if line.strip()]
    candidate = [json.loads(line) for line in args.candidate_output.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not (len(rows) == len(base) == len(candidate)):
        raise ValueError("benchmark and both output files must contain the same number of items")
    ids = [row["id"] for row in rows]
    if ids != [item["id"] for item in base] or ids != [item["id"] for item in candidate]:
        raise ValueError("item IDs are not aligned")

    rng = random.Random(args.seed)
    blind: list[dict[str, str]] = []
    mapping: list[dict[str, str]] = []
    for row, base_item, candidate_item in zip(rows, base, candidate):
        if rng.getrandbits(1):
            output_a, output_b = candidate_item["output"], base_item["output"]
            role_a, role_b = "candidate", "base"
        else:
            output_a, output_b = base_item["output"], candidate_item["output"]
            role_a, role_b = "base", "candidate"
        blind.append({"id": row["id"], "category": row["capability_family"], "prompt_tr": row["prompt_tr"], "output_a": output_a, "output_b": output_b})
        mapping.append({"id": row["id"], "a_role": role_a, "b_role": role_b})

    args.output_dir.mkdir(parents=True, exist_ok=True)
    jsonl = args.output_dir / "blind-review.jsonl"
    csv_path = args.output_dir / "blind-review.csv"
    mapping_path = args.output_dir / "blind-mapping-sealed.json"
    with jsonl.open("w", encoding="utf-8") as handle:
        for item in blind:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "category", "prompt_tr", "output_a", "output_b"])
        writer.writeheader()
        writer.writerows(blind)
    mapping_path.write_text(json.dumps({"seed": args.seed, "mapping": mapping}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "items": len(blind),
        "randomization_seed": args.seed,
        "benchmark_sha256": sha256(args.benchmark),
        "base_output_sha256": sha256(args.base_output),
        "candidate_output_sha256": sha256(args.candidate_output),
        "blind_jsonl_sha256": sha256(jsonl),
        "blind_csv_sha256": sha256(csv_path),
        "mapping_sha256": sha256(mapping_path),
        "protocol": "exp-002 scoring-rubric.md; identities excluded from review files",
    }
    (args.output_dir / "blind-review.manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
