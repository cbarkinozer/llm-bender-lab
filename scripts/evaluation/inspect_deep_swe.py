"""Download pinned DeepSWE evaluation data outside Git and report descriptive EDA.

Run from repository root with .venv/bin/python scripts/evaluation/inspect_deep_swe.py.
Requires accepted HF dataset access and local authentication. Executes no task code.
"""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shlex
import tomllib

from huggingface_hub import hf_hub_download
import pyarrow.parquet as pq

REVISION = "6d6f134460c137e24c6bb7e1e69954116ea9dbb3"
EXPECTED_SHA256 = "737e1b101d9556aa1b0fd66b8fefd436158a63b18d7105733739c79126fb495e"
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "experiments/unit-test-generation/qwen3.5-4b/exp-000-baseline/benchmark-audit/deep-swe-20261017"
CACHE = Path.home() / ".cache/llm-bender-lab/deep-swe" / REVISION


def main():
    # Project credentials may use HF_API_KEY rather than the Hub's HF_TOKEN.
    # Read only recognized token keys; never execute or print .env contents.
    if not os.environ.get("HF_TOKEN"):
        env_path = ROOT / ".env"
        credentials = {}
        if env_path.is_file():
            for line in env_path.read_text().splitlines():
                line = line.strip().removeprefix("export ")
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key.strip() in {"HF_TOKEN", "HF_API_KEY", "HUGGING_FACE_HUB_TOKEN"}:
                    parts = shlex.split(value, comments=True)
                    if parts:
                        credentials[key.strip()] = parts[0]
        for key in ("HF_TOKEN", "HF_API_KEY", "HUGGING_FACE_HUB_TOKEN"):
            if credentials.get(key):
                os.environ["HF_TOKEN"] = credentials[key]
                break
    path = Path(hf_hub_download(
        "datacurve/deep-swe", "data/test-00000-of-00001.parquet",
        repo_type="dataset", revision=REVISION, local_dir=CACHE,
    ))
    actual_hash = sha256(path.read_bytes()).hexdigest()
    if actual_hash != EXPECTED_SHA256:
        raise ValueError("Parquet SHA256 differs from pinned Hub LFS metadata")
    table = pq.read_table(path)
    rows = table.to_pylist()
    report = {
        "dataset": "datacurve/deep-swe", "revision": REVISION,
        "inspected_at": datetime.now(timezone.utc).isoformat(),
        "local_file": str(path), "sha256": actual_hash,
        "size_bytes": path.stat().st_size, "row_count": len(rows),
        "schema": str(table.schema), "columns": {},
        "exact_duplicate_rows": len(rows) - len({json.dumps(r, sort_keys=True, default=str) for r in rows}),
        "scope": "Descriptive parquet EDA only; no execution or semantic validation",
    }
    for name in table.column_names:
        values = [r[name] for r in rows]
        present = [v for v in values if v is not None]
        summary = {"null_count": len(values)-len(present),
                   "empty_string_count": sum(isinstance(v, str) and not v.strip() for v in present),
                   "types": dict(Counter(type(v).__name__ for v in present))}
        if present and all(isinstance(v, str) for v in present):
            lengths = sorted(len(v) for v in present)
            summary["character_lengths"] = {
                "min": lengths[0], "median": lengths[len(lengths)//2],
                "p90": lengths[min(len(lengths)-1, int(.9*len(lengths)))], "max": lengths[-1],
            }
            summary["distinct_count"] = len(set(present))
            if name.lower() in {"language", "repo", "repository", "split", "difficulty"}:
                summary["counts"] = dict(Counter(present))
        report["columns"][name] = summary
    report["distributions"] = {
        name: dict(Counter(str(r[name]) for r in rows))
        for name in ("language", "category", "allow_internet", "cpus", "memory_mb",
                     "storage_mb", "agent_timeout_sec", "verifier_timeout_sec")
        if name in table.column_names
    }
    report["repository_count"] = len({r["repo"] for r in rows})
    report["duplicate_task_ids"] = {k: v for k, v in Counter(r["task_id"] for r in rows).items() if v > 1}
    report["duplicate_prompts"] = sum(v-1 for v in Counter(r["problem_statement"] for r in rows).values())
    inventory = []
    for row in rows:
        metadata = tomllib.loads(row["task_toml"])
        paths = [line[6:].split("\t")[0] for line in row["reference_patch"].splitlines()
                 if line.startswith("+++ b/")]
        inventory.append({
            "task_id": row["task_id"], "language": row["language"], "repo": row["repo"],
            "title": row["display_title"], "base_commit": row["base_commit"],
            "prompt_characters": len(row["problem_statement"]),
            "reference_patch_characters": len(row["reference_patch"]),
            "reference_patch_files": paths,
            "reference_patch_suffixes": dict(Counter(Path(p).suffix for p in paths)),
            "toml_language": metadata.get("metadata", {}).get("language"),
            "image_pinned_by_digest": "@sha256:" in row["docker_image"],
        })
    report["task_inventory"] = inventory
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "parquet-eda.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"rows": len(rows), "columns": table.column_names,
                      "report": str(OUTPUT / "parquet-eda.json")}, indent=2))


if __name__ == "__main__":
    main()
