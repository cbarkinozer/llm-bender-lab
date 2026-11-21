# exp-000-baseline

## Status
paused by the owner on 2026-11-21 (no inference has run). Kaggle auth works and the real
harness was found (see "Harness facts" in `../README.md`); the work resumes only with a Vast.ai instance
and a Kaggle token on it.

## Goal
Measure untouched Gemma 4 E4B in the competition harness on the public tasks, with variance,
and classify its failures. No training.

## Hypothesis
With the organizer's default agent config, E4B solves roughly 10-14% of tasks (other participants report
~14% zero-think on a 114-task local set; the public leaderboard shows small models at 0.08-0.12). Most
failures are empty patches, timeouts, bad tool-call JSON and wrong-file edits rather than reasoning.

## Parent Experiment
none

## What Changed
Nothing. This is the reference every later experiment is compared against.

## Base Model
`gemma-4-e4b-it-qat-w4a16-ct`, no adapter. Revision/hashes to be pinned at download.

## Dataset
Public `tasks.jsonl` (129 tasks, 4 Python repos). Develop on fastapi, requests, httpx; hold out rich.
See `config.yaml`.

## Training Setup
none

## Evaluation
Pass@1 per seed (0-4), report mean, SD and per-repo breakdown with all tasks in the denominator.
Per-item outputs, tool-call traces and failure classes are saved. Verifier preflight: gold patch passes,
empty patch fails (target at least 124 of 129 scorable).

## Results
none yet

## Regressions
n/a

## Conclusion
pending

## Next Step
1. Done: Kaggle auth, `HARNESS_README.md` and `tasks.jsonl` read and pinned in `config.yaml`.
2. On vast.ai: install the official wheelhouse (`metric/gemma-4-developer-agent-wheelhouse`: swegemma, adk-submission,
   adk-eval-core, vllm 0.19.1), download snapshots/wheels and the E4B model
   (`google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`), smoke-test with `swegemma eval`.
3. Run the baseline seeds, then write results here and update the registry in `../README.md`.
