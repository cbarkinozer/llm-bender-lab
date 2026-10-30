> Current review, 2026-10-31: [revision 05](app-core-v05/README.md).
> Code display is HTML-escaped, the new meta-text defect category is available,
> and numbering/process-text/preservation pre-checks pass. Review:
> http://127.0.0.1:7900/dataset/ae9c43c9-54ea-4602-9d4d-56741869b59a/annotation-mode
> Previous datasets and annotations remain preserved; no SFT has started.

> Current format revision, 2026-10-31: [app-core-v04](app-core-v04/README.md).
> Natural requests and shared system instructions are separated from construction/review metadata.
> Tests and application behavior match v03; record-specific executor work is archived separately.
> Review: http://127.0.0.1:7900/dataset/7500c36b-0971-41bd-91c5-765d6e7add5e/annotation-mode
> Earlier status blocks below are history. No whole-app SFT has run.

> Current revision, 2026-10-30: [app-core-v03](app-core-v03/README.md) supersedes
> the candidate suites below. Human approval is required again. Review:
> http://127.0.0.1:7900/dataset/f7c79cb7-8943-4281-98d1-4e9128a2b529/annotation-mode
> Fixed interface/decision sections, coverage maps, rationale, explicit manual gaps,
> 142 passing reference cases, 57 targeted kills and complete 8K measurements.
> Older review waivers/results below are preserved history, not current instructions.

# Quick thinking-SFT demo: requirements to pytest

Active owner scope, 2026-10-29: learn by completing a small useful demo. The paper
continuation is paused. Use untouched Qwen3.5-4B with thinking enabled locally;
then train thinking plus final pytest output and repeat the same evaluation.

## Latest result: compact candidate suites

Owner review was waived. [app-core-v02](app-core-v02/README.md) contains the
assistant review, table-free maps, nine executable candidate suites and exact
counts: 108 passing cases, 11,765 Qwen output tokens total, largest output 4,649.
Whole-app coverage gaps remain explicitly listed; no SFT started.
Current Argilla: http://127.0.0.1:7900/dataset/9eec1313-018c-4885-aa7a-7f7dc38b5110/annotation-mode

## Current step: whole-app request and core-test maps

The owner has changed the active scope to nine natural whole-app requests with
compact core acceptance suites. Review [app-briefs-v01](app-briefs-v01/README.md):
http://127.0.0.1:7900/dataset/ee48112d-5b2a-4626-9fd1-ada50f8f0f6b/annotation-mode

Nine paragraphs and 53 proposed mappings are published. These are drafts, not
approved SFT targets or fully executed whole-app acceptance suites. Next: owner
scope/clarification review, split-role assignment, core suite selection/creation,
validation and final token measurements. Old questions-v02 and baseline-v01 are
preserved historical pilots, not measurements of the new whole-app prompts.

## Original ten evaluation examples

`requirements.jsonl` contains ten assistant-authored English requirements with
explicit public APIs. Topics: bookings, money allocation, retries, pagination,
configuration patching, business dates, intervals, inventory events, CSV and pricing.
Input is requirement/API only; output is pytest. These ten examples are excluded
from training. Separate examples will teach the same skills without copying these
contracts. No publication-scale benchmark, exhaustive taxonomy or downstream code
generation experiment is required for this demo.

## Progress

- Contracts clarified before inference; identities recorded in `task-audit.json`.
- Ten reference contract checks pass; ten deliberately faulty implementations
  each have a passing-reference/failing-fault witness. Checks are assistant-authored
  and limited; they are not proof the references are flawless.
- Baseline `baseline-20261030-v01` started locally on 2026-10-30; no SFT yet.
  Outputs: `/Users/cbarkinozer/Documents/llm-bender-artifacts/thinking-tdd/baseline-20261030-v01`.
  Direct llama.cpp HTTP, Q4_K_M, 16384 context, 8192 shared thinking/answer
  output cap, temperature 0.6, top-p 0.95, top-k 20, repetition penalty 1.05,
  seed 42. One attempt, no adaptive budgets or repairs.
  `scripts/evaluation/run_thinking_tdd_demo.py` preserves requests/SSE events,
  reasoning, answer, stop reason and usage.
  `grade_thinking_tdd_demo.py` runs suites in isolated Docker;
  `review_thinking_tdd_demo.py` appends completed results to Argilla.
  Review: http://127.0.0.1:7900/dataset/3c19892f-0321-45c8-9eda-0583ec60d3d1/annotation-mode
  Check saved `summary.json` and `grades.json` for actual completion; this
  start record does not claim all ten have finished. Native/nonquantized
  deployment will need a fresh matched baseline if used for SFT comparison.

`verifier/` is private grading context: never include references, faults or witnesses
in generation prompts. Run model-generated suites only in isolated Docker.

## Short completion path

1. Run one local thinking-on baseline per task and save reasoning, pytest, token
   counts and termination. Use one fixed budget; report truncations as failures.
2. Score correct-reference passing and fault detection. Review expectation
   correctness and useful assertions; use Argilla for owner annotation.
3. Prepare a small separate set of verified reasoning-plus-pytest demonstrations.
   Validate the native chat template and assistant loss on reasoning and answer.
4. Run a short LoRA SFT, verify adapter loading, and rerun these ten unchanged tasks.
5. Report before/after counts honestly, preserve artifacts, and move to GRPO.
   This tiny demo can demonstrate a measured local gain, not broad generalization.

Smoke command (trusted grading code only):

```sh
.venv/bin/python -m pytest -q experiments/unit-test-generation/qwen3.5-4b/exp-001-local-thinking-10/verifier/test_references.py experiments/unit-test-generation/qwen3.5-4b/exp-001-local-thinking-10/verifier/faults.py
```
