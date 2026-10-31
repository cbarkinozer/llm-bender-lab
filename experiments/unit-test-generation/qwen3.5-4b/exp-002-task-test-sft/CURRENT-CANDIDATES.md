> Active review fixes: [REVIEW-FIXES.md](REVIEW-FIXES.md). Planning v04 fixes shared-file ordering; current preview is intent-only-preview-v02 and baseline packet is baseline-reliability-v03. Counts are unchanged. Older revision descriptions below are preserved history.

> Current content review: [CONTENT-REVIEW.md](CONTENT-REVIEW.md). Active planning/decision revisions are v03. Source implementation is excluded from model inputs and targets; audit columns are excluded by an explicit export allowlist. Counts remain 95 total / 78 train-family candidates. Training and inference have not run.

> Current quality revision: [candidate-index-v02.json](candidate-index-v02.json) replaces the preflight row with a valid-data control; count remains 58. [RELIABILITY-PREPARATION.md](RELIABILITY-PREPARATION.md) records 22 separate decision drafts and prepared baseline inputs. Current training-candidate totals are 91858 full tokens, 15597 answer tokens and 1419 rationale tokens. Earlier totals below describe the original selection.

# Current candidate data and planning track

The test-generation dataset has **58 executable candidates: 50 train, 5 development, 3 holdout**. This consists of the unchanged 38-row pilot-v02 and 20 new external-batch-v02 rows. The two original whole-app evaluation families remain reserved and are not added to the training data. Split roles remain proposed pending semantic overlap review and protocol freezing. All rows remain training_eligible=false; no model run has started.

## External test batch

- 20/20 reference suites pass: 67 collected cases.
- 40/40 targeted faults detected by explicit call-phase assertions/pytest failures; collection errors and runtime TypeErrors do not count as kills.
- Three shuffled-order runs per task (seeds 17, 43, 91) pass.
- New source families: LiteCLI and tldr train; Posting development; ddgr holdout.
- Tests and rationale are newly authored; upstream tests were not copied. Pinned source files, source/license hashes, notices, environment versions, actual execution logs and fault definitions are retained.
- Reference adapters: LiteCLI gets minimal distribution metadata for import; Posting uses an empty package initializer to avoid unrelated terminal UI imports; ddgr's unchanged extensionless script is exposed as ddgr.py. Selected behavior code remains unchanged. This verifies those components, not full application installation or integration.
- Host subprocesses run trusted authored fixtures with credentials filtered and a 45-second runtime bound. This is not an OS network sandbox. Untrusted model outputs still require the protected execution path.

`external-batch-v01` preserves the initial failed run (missing LiteCLI metadata, a ddgr method/property mistake and diagnostic-probe problems). In v02, the initial nested-query expectation failed against LiteCLI. The current table task explicitly excludes nesting and tests INSERT target identification without constraining its alias value. Prior records and logs remain under repairs/evidence. No upstream source was changed to force a pass.

All 58 candidates have unique exact normalized test ASTs and no source-family split crossing. Semantic near-duplicate/requirement review is still pending; passing targeted probes is not exhaustive correctness or annotation approval. Public upstream projects may have appeared in pretraining, so repository separation alone does not establish pretraining novelty.

## Planning track

`planning-pilot-v02` contains **15 separate planning drafts**, over 11 source families: 13 proposed train, 1 development and 1 holdout. Four rows are focused variants of an existing family. Plans and their child tasks inherit the same role. These are transformations of agreed inventories, not independently observed successful planner trajectories, and they are not added to the test-only training dataset.

Each target states intent, task dependencies, implementation/test files, acceptance criteria, interfaces, child prompts, deferred questions and completion gates. Shared interface contracts occur once in the plan; an explicit dispatch rule attaches the full contract to each child prompt. Materialized child inputs are saved for sufficiency review. Tasks that edit shared files must execute sequentially.

Structural checks cover unique IDs, dependency closure and acyclicity. All 15 native full sequences fit 8192 tokens (maximum 3632). Requirement coverage, sensible decomposition, unnecessary implementation decisions, interface consistency, child-prompt sufficiency and native loss labels still need review. Earlier planning-pilot-v01 is preserved: three overlong outputs repeated whole interfaces per task. The current representation removes repetition without truncating contracts.

## Recommendation

Keep the primary experiment task-to-tests. A small SFT demo with 50 training candidates is reasonable to test, but its utility is unmeasured. They contain 91997 full-conversation tokens, including 15398 answer tokens and 1414 rationale tokens before label auditing; input context dominates. Repetition changes exposure, not diversity. Do not infer that a few epochs will generalize from this token count.

Review the planner drafts as a second capability, then compare test-only training against planning-plus-tests with the same test evaluation, fixed total supervised-token budget and separately reported planner metrics. This is a separate experimental hypothesis, not a reason to relabel the test-only run or count planning drafts toward 100 test examples. Choose checkpoints with development data; keep final holdout results out of training choices.

Next work: review the 20 test contracts and 15 plans, check semantic overlaps, audit token labels, freeze family roles and generation/scoring protocol, and measure the unchanged starting model before training. Additional repositories should fill demonstrated behavior gaps rather than an arbitrary row target.

Artifacts:

- `external-batch-v02/share/twenty-external-task-examples.txt` (separated by ----)
- `external-batch-v02/validation-report.json`
- `planning-pilot-v02/fifteen-planning-drafts.txt` (separated by ----)
- `planning-pilot-v02/materialized-child-inputs.jsonl`
- `CANDIDATE-SUMMARY.json`
