[Original-source CC report](original-source-complexity-v02/REPORT.md): mean 5.44, population std 7.85 across 2412 original non-test functions. See [complexity correction](COMPLEXITY-CORRECTION.md) for the superseded class-method counting issue.

## Dataset details

[DATASET-PROFILE.md](DATASET-PROFILE.md) reports token mean/std, complexity, domains, behavior coverage and semantic overlap. [Open the interactive dashboard](dataset-profile-v02/dashboard.html) or [download per-record CSV](dataset-profile-v02/records.csv). No training selection changed.

> Native-label audit now passes for the active 78-candidate projection. See [NATIVE-LABEL-AUDIT.md](NATIVE-LABEL-AUDIT.md) for actual masks, token counts and scope. Trainer parity, semantic overlap review and runtime baseline remain pending. Older pending-audit statements below describe prior state.

> Active review fixes: [REVIEW-FIXES.md](REVIEW-FIXES.md). Planning v04 fixes shared-file ordering; current preview is intent-only-preview-v02 and baseline packet is baseline-reliability-v03. Counts are unchanged. Older revision descriptions below are preserved history.

> Current content review: [CONTENT-REVIEW.md](CONTENT-REVIEW.md). Active planning/decision revisions are v03. Source implementation is excluded from model inputs and targets; audit columns are excluded by an explicit export allowlist. Counts remain 95 total / 78 train-family candidates. Training and inference have not run.

## Reliability preparation

[RELIABILITY-PREPARATION.md](RELIABILITY-PREPARATION.md) records a confirmed reject-all survivor and its checked fix, 22 separate clarification/integrity drafts, and 17 prepared baseline requests. The active test selection is [candidate-index-v02.json](candidate-index-v02.json), still 58 tasks. Baseline inference and training have not run.

## Current candidate batches

[CURRENT-CANDIDATES.md](CURRENT-CANDIDATES.md) records 58 executable test candidates (50 train, 5 development, 3 holdout), including 20 checked external examples, plus a separate 15-row planning draft track. Planning rows are excluded from test-only SFT. No model baseline or training has run. See [CANDIDATE-SUMMARY.json](CANDIDATE-SUMMARY.json) for counts and tokens.

> Current expansion: pilot-v02 contains 38 task artifacts across all seven training families and supersedes the eight-row pilot-v01. See [EXPANSION-RESULTS.md](EXPANSION-RESULTS.md) for execution status and measured counts. The source catalog has 62 additional unbuilt proposals; it is not a 100-example training dataset. The initial pilot description below is preserved history.

# Task-to-tests thinking SFT

Active direction, 2026-10-31. The owner accepted a task-level workflow: application
request, explicit plan and interfaces, selected task, tests, implementation and
execution feedback. Whole-app v07 remains preserved under exp-001.

## Hypothesis and scope

Fine-tuning Qwen3.5-4B on verified, task-sized reasoning-plus-pytest demonstrations
will improve requirement-faithful test generation on separate application families.
Planning and implementation generation remain outside the first SFT objective.
Neither an executable training recipe nor a model baseline has been run here.

The initial deliverable is a format pilot, not a completed 100-task dataset:

- Two explicit application planning contexts, excluded from SFT labels.
- Eight task-to-test candidate conversations from two existing training families.
- Each input includes the natural app request, todo dependencies and file paths,
  selected task, acceptance criteria and a public interface contract.
- Each assistant target includes concise authored rationale and exactly one complete
  pytest file. No application implementation, private grader or execution evidence
  is included in model input. Files to implement are visible in the plan, not
  available only inside thinking text.
- Browser/packaging delivery tasks remain explicit in the plans but currently have
  no teaching demonstrations. The pilot does not silently claim full app coverage.

Read `pilot-v01/manifest.json` and `validation-report.json` for measured counts.
The shareable packet is `pilot-v01/share/task-test-pilot-v01.txt`; its eight
examples are separated by `----`. `planning-contexts.jsonl` contains the two
separate planning examples. These are authored contexts, not captured agent runs.

## Training sequence

1. Validate this task format on two application families (pilot-v01).
2. Complete the diversity/source-selection work in `DATASET-PLAN.md`; freeze
   repository/family roles before authoring related tasks.
3. Expand toward 100 training tasks, with separate development and final evaluation
   families. Planning records and repair turns do not inflate independent-task counts.
4. Freeze the deployment/evaluation protocol and run a new untouched-model baseline.
   Old whole-app outputs are not a baseline for this new task distribution.
5. Inspect actual native labels: reasoning, answer and EOS supervised; prompt and
   padding masked. Run smoke/tiny-overfit checks before the short LoRA experiment.
6. Repeat matched task evaluation. Later, compare an unchanged implementer with and
   without generated tests, graded by independent private requirements tests.

The existing AI-review preference persists. A new full human annotation round is
not required. However, changed task framing has not inherited v06/v07 reviewer
approvals; executable checks and semantic review are distinct.

## Reproduce the pilot

From repository root, using the previously prepared external environment:

```powershell
$env:PYTHONUTF8 = '1'
$env:USE_TORCH = '0' # Tokenizer-only preparation; unset for a later model run.
python scripts/evaluation/task_test_pilot.py build --tokenizer C:/Users/barkin/Documents/llm-bender-artifacts/tdd-v07-windows/tokenizer
python scripts/evaluation/task_test_pilot.py validate --python C:/Users/barkin/Documents/llm-bender-artifacts/tdd-v07-windows/.venv/Scripts/python.exe --source-root C:/Users/barkin/Documents/llm-bender-artifacts/tdd-v07-windows/sources
python scripts/evaluation/task_test_pilot.py export
```

Build refuses to overwrite an existing record set. A changed source spec requires
a new pilot revision, not silent replacement of reviewed examples. Validation
retains timestamped evidence. Only trusted authored fixtures run on the host;
untrusted model outputs still require the protected executor. The local executor
strips credentials and bounds time; mocks do not constitute OS network isolation.

Parent source/test hashes, native tokenizer/template hashes, per-task faults,
logs and seeded orders are recorded. References stay in the old validation/source
locations outside model-visible context. No paid compute or model weights are
required for this format pilot.

## External application audit

[EXTERNAL-APP-AUDIT.md](EXTERNAL-APP-AUDIT.md) records four pinned external apps and 20 source-backed task proposals (12 train, 5 development, 3 holdout proposed). No new SFT rows were created; the current pilot remains 38 drafts. Split roles remain proposals.
