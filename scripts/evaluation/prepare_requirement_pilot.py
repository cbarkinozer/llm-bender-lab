"""Prepare a bounded requirements-first development shortlist, never training data."""
from hashlib import sha256
import json
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
REVISION = "6d6f134460c137e24c6bb7e1e69954116ea9dbb3"
EXPECTED = "737e1b101d9556aa1b0fd66b8fefd436158a63b18d7105733739c79126fb495e"
CACHE = Path.home() / ".cache/llm-bender-lab"
OUTPUT = ROOT / "experiments/unit-test-generation/qwen3.5-4b/exp-000-baseline/requirements-pilot"
TASK_IDS = [
    "adaptix-name-mapping-aliases", "mashumaro-flattened-dataclass-fields",
    "cattrs-partial-structuring-recovery", "tomlkit-toml-table-converters",
    "returns-validated-error-accumulation", "sqlfmt-create-table-ddl-formatting",
    "sqlite-utils-safe-import-checkpoints", "httpx-streaming-json-iteration",
    "bandit-structured-nosec-directives", "vulture-persistent-analysis-cache",
    "narwhals-rolling-window-suite", "skrub-duration-encoding",
    "python-statemachine-state-data-scoping", "fastapi-implicit-head-options",
    "textual-kitty-key-phases", "dateutil-rfc5545-timezone-interop",
    "igel-persist-feature-schema", "aiomonitor-task-snapshots-diff",
    "ipython-session-bundle-replay", "kombu-virtual-queue-dead-lettering",
]

TEST_INSTRUCTION = """Generate Python pytest tests from the English requirement below BEFORE any implementation.
Return only one fenced python block containing a complete test module. Do not implement
the feature, include production code, weaken expectations to match existing behavior,
or use skip/xfail. Test the intended public behavior, with deterministic isolated
inputs, meaningful assertions and readable names. Use the public interfaces explicitly
named in the requirement; do not invent undocumented import paths or error classes.
If an expectation or interface is underspecified, leave a brief comment identifying
the ambiguity instead of inventing a requirement. Test normal behavior, relevant
boundaries and explicitly specified failures. Group related assertions coherently.
Tests may fail on the original repository because the requested feature is new.
Implementation and private grading artifacts are deliberately unavailable.

Repository: {repo}
Base commit: {base_commit}

ENGLISH REQUIREMENT (verbatim benchmark problem statement):
{requirement}
"""


def main():
    parquet = CACHE / "deep-swe" / REVISION / "data/test-00000-of-00001.parquet"
    if sha256(parquet.read_bytes()).hexdigest() != EXPECTED:
        raise ValueError("Unexpected dataset hash")
    rows = pq.read_table(parquet).to_pylist()
    by_id = {r["task_id"]: r for r in rows}
    if len(by_id) != len(rows):
        raise ValueError("Duplicate task IDs")
    selected = [by_id[k] for k in TASK_IDS]
    if len({r["repo"].removesuffix(".git").rstrip("/") for r in selected}) != 20:
        raise ValueError("Pilot must contain 20 different repositories")
    packets = CACHE / "requirements-pilot-v01"
    packets.mkdir(parents=True, exist_ok=True)
    inventory = []
    for row in selected:
        prompt = TEST_INSTRUCTION.format(repo=row["repo"], base_commit=row["base_commit"],
                                       requirement=row["problem_statement"])
        task_dir = packets / row["task_id"]
        task_dir.mkdir(exist_ok=True)
        for name, content in {"requirement.md": row["problem_statement"],
                              "tests-first-prompt.md": prompt}.items():
            path = task_dir / name
            if path.exists() and path.read_text() != content:
                raise ValueError(f"Refusing to overwrite changed packet: {path}")
            path.write_text(content)
        inventory.append({
            "task_id": row["task_id"], "repo": row["repo"], "base_commit": row["base_commit"],
            "requirement_sha256": sha256(row["problem_statement"].encode()).hexdigest(),
            "prompt_sha256": sha256(prompt.encode()).hexdigest(),
            "requirement_characters": len(row["problem_statement"]),
            "packet_directory": str(task_dir), "status": "candidate: interface/contract preflight pending",
        })
    manifest = {
        "source": "datacurve/deep-swe", "revision": REVISION, "parquet_sha256": EXPECTED,
        "purpose": "requirements-first development pilot; evaluation only, never SFT/GRPO training",
        "selection": "20 explicit task IDs; one task per repository; public API/behavior diversity; selected before model outputs",
        "not_a_random_sample": True,
        "status": "provisional shortlist; not a runnable or validated benchmark",
        "model_visible_fields": ["problem_statement", "repo", "base_commit"],
        "held_back_fields": ["reference_patch", "test_patch", "verifier_script", "task_toml"],
        "transfer_holdout_exclusion_repositories": sorted(r["repo"] for r in selected),
        "tasks": inventory,
        "unselected_python": [
            {"task_id": r["task_id"], "reason": "language label conflicts with TypeScript reference patch"
             if r["task_id"] == "koota-entity-snapshot-rollback"
             else "additional same-repository task" if r["repo"] in {t["repo"] for t in selected}
             else "deferred to keep the development pilot bounded at 20"}
            for r in rows if r["language"] == "python" and r["task_id"] not in TASK_IDS
        ],
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "candidate-manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps({"candidates": len(inventory), "manifest": str(OUTPUT / "candidate-manifest.json"),
                      "packets": str(packets)}, indent=2))


if __name__ == "__main__":
    main()
