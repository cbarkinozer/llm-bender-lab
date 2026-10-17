# DeepSWE inspection — 2026-10-17

## Freshness decision

Owner accepts dataset release after the stated Qwen3.5-4B date, 2026-03-09,
as sufficient evidence for this research. Underlying open-source code may have
been seen; exhaustive exposure investigation is not required and is not a blocker.
Repository API creation date is **2026-06-01T21:58:03Z**, 84 days later.
This is repository creation evidence, not independently verified first publication
of every task. The model date is owner-supplied, not a verified training cutoff.

## Download and provenance

- [Dataset/card](https://huggingface.co/datasets/datacurve/deep-swe).
- Pinned revision: `6d6f134460c137e24c6bb7e1e69954116ea9dbb3`.
- Repository last modification: `2026-06-02T19:31:16Z`.
- Requested parquet: `data/test-00000-of-00001.parquet`, **1,577,612 bytes**.
- Expected SHA256 from Hub LFS metadata:
  `737e1b101d9556aa1b0fd66b8fefd436158a63b18d7105733739c79126fb495e`.
  The downloaded parquet matches this SHA256.
- Card downloaded to
  `/Users/cbarkinozer/.cache/llm-bender-lab/deep-swe/6d6f134460c137e24c6bb7e1e69954116ea9dbb3/README.md`.
- Initial unauthenticated request returned HTTP 401. The owner then confirmed access;
  the project `.env` `HF_API_KEY` validated successfully and the parquet downloaded.
  The inspection script now automatically reads recognized token keys without
  printing or persisting credentials. No new token or global login was needed.
- `metadata-inventory.json` records file paths/sizes, task IDs, expected LFS hashes,
  dates, card hash and download status. Raw task content stays outside Git.

## Card and public file-inventory findings

- Card describes **113 tasks** across TypeScript, Go, Python, JavaScript and Rust;
  instructions are English. Public inventory independently has 113 task directories
  and 800 files. Measured counts are Go 34, Python 34, TypeScript 35, Rust 5 and JavaScript 5.
  One Python label is inconsistent with the reference patch (see below).
- Card metadata declares one `test` split and labels the corpus held-out evaluation
  data. Use for evaluation, not GRPO training. Retire any inspected/adapted pilot
  tasks from the later independent transfer holdout, preferably grouping by repository.
- Harbor-format tasks have `instruction.md`, `task.toml`, environment Dockerfile,
  private verifier patches/scripts and reference solutions. Model input should be
  instruction plus permitted repository context, not verifier or reference patch.
- These are feature/repair engineering tasks, not ready-made prompts to test an
  already correct function. Ordinary test-generation adaptation needs a validated
  implementation and a rewritten test-only instruction; report adapted results
  separately from original DeepSWE scores.
- Card describes behavioral grading and Pier/mini-swe-agent runs on Modal. Pi is
  a harness adaptation. Native Mac ARM64 support and runnable images are unverified.
- Downloaded card has no `license` field or explicit license section. Record actual
  applicable terms before redistributing content; the access checkbox says evaluation.

## Completed descriptive EDA

- 113 rows, 23 columns, 92 distinct repository URL strings (card describes 91
  repositories; URL normalization/benchmark-version differences remain unresolved).
- No null fields, empty text fields, duplicate task IDs, exact duplicate rows or
  exact duplicate problem statements. This is not a semantic near-duplicate audit.
- Categories: 106 feature requests, 4 bug fixes, 3 enhancements.
- Prompt lengths: 471–5,385 characters, median 1,975, p90 3,450. Character counts
  are not tokenizer counts. Reference patches: median 26,288 characters.
- All tasks specify no internet, 2 CPUs, 8,192 MB memory, 20,480 MB storage,
  5,400-second agent timeout and 1,800-second verifier timeout. These are configured
  limits, not measured usage; use one task at a time initially on the Mac.
- None of the 113 supplied task image names is pinned by digest. ARM64 image
  manifests and runtime compatibility have not been verified.
- **Label anomaly:** `koota-entity-snapshot-rollback` is marked Python both in the
  row and TOML, but all six reference-patch paths are `.ts`. Exclude it from a
  Python-only pilot pending correction. The other 33 Python-labeled rows include
  Python reference-patch paths, which alone does not establish runtime suitability.
- Columns include problem statement, source repository/base commit, Dockerfile,
  resource limits, hidden verifier script/test patch and reference patch. The
  original task asks for implementation work. For ordinary test generation, prepare
  and validate the intended implementation first, keep it read-only, and give the
  model a test-only instruction. Keep hidden grading tests/solutions out of prompts.
- Original verifier inspection shows hidden test-patch application plus baseline
  and new-test execution. That verifier grades implementation, not our test-quality
  taxonomy; it cannot directly substitute for unit-test-suite quality evaluation.

`parquet-eda.json` contains measured schema, field summaries, distributions and
per-task metadata/patch-path inventory. Raw parquet remains in the external cache.
No reference patches, test patches or raw prompts were copied into the report.
No task code, generated tests or models were executed; semantic correctness,
reference health and environment feasibility remain unmeasured.

## Reproduce

From repository root:

```sh
.venv/bin/python scripts/evaluation/inspect_deep_swe.py
```

The script uses an existing HF_TOKEN or recognized project `.env` token key,
verifies the pinned parquet SHA256, and writes descriptive EDA without executing
code from the dataset. Next inspect the 33 Python candidates to select a bounded
20-task pilot, with independent implementation/runtime checks. Keep those tasks
and related repository groups separate from final broader-SWE transfer evaluation.
