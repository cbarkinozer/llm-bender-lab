Current label-audit update: native-label-audit-v01 now contains actual input_ids/attention_mask/labels for the active 78 preview rows, with verified masks and pinned tokenizer identity. Read NATIVE-LABEL-AUDIT.md in the experiment directory. Trainer parity remains pending; earlier no-script/pending-label statements below are historical.

Current follow-up: the independent review is preserved in the experiment directory. Read REVIEW-FIXES.md there for the v04 ordering corrections and evidence before beginning another review.

# Local agent handoff: independently check the intent-driven TDD data

You are taking over an existing workspace. Independently inspect the actual artifacts and report defects. Do not assume the previous assistant's summaries or checks establish correctness.

## Workspace and first reads

Repository on this machine:

`C:\Users\barkin\Documents\GitHub\llm-bender-lab`

Active experiment, abbreviated below as `EXP`:

`experiments/unit-test-generation/qwen3.5-4b/exp-002-task-test-sft/`

Read `AGENTS.md`, the relevant dataset/evaluation/reproducibility documentation, and these files first:

- `EXP/config-planned.json`
- `EXP/CONTENT-REVIEW.md`
- `EXP/CANDIDATE-SUMMARY.json`
- `EXP/candidate-index-v03.json`
- `EXP/RELIABILITY-PREPARATION.md`

The working tree contains substantial intentional uncommitted work. Preserve it. Old versions are historical evidence; do not reset the checkout or overwrite them. Prefer the active config/index over older README sections. This handoff describes expected state; verify it against disk.

## What the owner wants

Train a small model to help turn a natural-language request for a small application into a reliable test-first development workflow:

1. Understand user intent.
2. Recognize unresolved behavior; ask targeted questions when the answer affects observable requirements.
3. Proceed autonomously on routine implementation choices and sufficiently clear requirements.
4. Divide the application into tasks with dependencies, file ownership, proposed public interfaces and objective acceptance criteria.
5. Materialize useful file-level prompts and generate requirement-based pytest tests.
6. Eventually support real execution, integration checks, diagnosis, replanning and cleanup. We do not yet have captured agent trajectories teaching that full loop.

The final product ambition is small-app delivery. The first experimental hypothesis is narrower: task-to-tests. Planning and clarification/integrity are separate candidate tracks; they are not automatically mixed into that experiment.

### Mandatory source-code boundary

**Repository implementation source must never appear in model inputs or training targets.** Source/reference columns may exist for audit and trusted reference execution, but must not be serialized into training conversations. Never stringify the complete rich record or concatenate its audit/source fields into a prompt.

Generated pytest code is an intended target. Necessary synthetic fixtures and code snippets used as test inputs are allowed. Interface signatures and behavioral contracts can be explicit task context or clearly labeled design proposals. Do not confuse these with permission to supply repository implementation solutions.

The owner prioritizes intent understanding over learning to copy source code. Watch for source-derived implementation details silently presented as user requirements, even when no source body is pasted. Internal design choices may be proposed; user-visible policies must be grounded or clarified.

## Expected current inventory

| Track | Total | Train-family candidates | Development | Holdout |
|---|---:|---:|---:|---:|
| Test generation | 58 | 50 | 5 | 3 |
| Planning | 15 | 13 | 1 | 1 |
| Clarification and test integrity | 22 | 15 | 3 | 4 |
| Total | 95 | 78 | 9 | 8 |

These are candidate counts, not 95 independent applications. The planning set spans 11 source families and includes four focused variants. Decision examples reuse existing families. Preserve family/upstream/near-duplicate separation across every track. Two original whole-app evaluation families, GitHub-insignia and slm_test_generation, remain reserved and must not enter training.

All training flags remain disabled. No starting-model inference baseline or fine-tuning has run. Source/reference executions are not model evaluations. The author also performed the existing content review; it is not independent approval.

## Active artifacts

Paths here are relative to `EXP`.

- `quality-audit-v01/current-test-candidates.jsonl`: materialized active 58 test candidates.
- `candidate-index-v03.json`: selection/provenance, replacing only the preflight row.
- `pilot-v02/records.jsonl`: original 38 candidates, preserved.
- `external-batch-v02/records.jsonl`: 20 external candidates, preserved.
- `quality-preflight-v01/records.jsonl`: corrected preflight example replacing its original row; **not** an additional example.
- `quality-audit-v01/adjudication.json`: concrete defect evidence and scope limitations.
- `planning-pilot-v04/records.jsonl`: active 15 planning examples.
- `planning-pilot-v04/materialized-child-inputs.jsonl`: prompts children would actually receive.
- `planning-pilot-v04/content-review.json`: prior review decisions.
- `reliability-pilot-v03/records.jsonl`: active 22 decision examples: 12 clarification, 10 integrity.
- `reliability-pilot-v03/content-review.json`: 14 retained, 8 revised in the prior review.
- `intent-only-preview-v02/*-train-preview.jsonl`: 50 test, 13 plan and 15 decision conversations, in separate files. Only `messages` is exported, with role/content and optional assistant reasoning_content. This is a projection preview, not a runnable mixed SFT recipe.
- `intent-only-preview-v02/audit-index.json`: provenance kept outside model-visible records.
- `baseline-reliability-v03/requests.jsonl`: 17 model-facing evaluation requests, without reference answers.
- `baseline-reliability-v03/scoring-references.jsonl`: grader-only targets; never send these to the evaluated model.
- `baseline-reliability-v03/rubric.json` and `protocol.json`: proposed scoring and incomplete runtime protocol. Backend/decoding settings remain unset.

Human-readable packets, separated by `----`, are available as `planning-pilot-v04/review-examples.txt`, `reliability-pilot-v03/review-examples.txt`, and `baseline-reliability-v03/requests-for-model.txt`.

## Independent checks to perform

### 1. Source exclusion and serialization

Inspect the actual model-visible text in all 78 preview records, not just their top-level keys. Confirm that application implementation bodies, solution snippets, mutation probes, grader answers and execution logs did not get embedded in message content. An allowlist prevents column leakage but cannot establish semantic cleanliness of arbitrary content.

Verify `scripts/evaluation/export_intent_only_preview.py` preserves only intended fields and rejects development/holdout rows. Test with source sentinels in extra columns and nested message metadata. Preserve pytest targets and authored rationale; do not remove them merely because they contain code.

Check provenance separately. Do not accidentally treat audit metadata or materialized child inputs as new independent SFT targets.

### 2. Planning quality, all 15 records

- Does the plan cover the user's requested scope, including delivery, or clearly honor an explicitly narrower milestone?
- Are actual user requirements separated from proposed APIs and design preferences?
- Are questions necessary, targeted and answerable? Avoid teaching a blocking question for every harmless internal choice.
- Can independent tasks proceed while an unrelated question is pending? Check whether each unresolved decision's impact on tasks is clear.
- Are dependencies complete, acyclic and meaningful? Are shared-file edits serialized?
- Inspect materialized child prompts: enough contract and acceptance context, no hidden implementation, no missing interface references, no unresolved behavior treated as settled.
- Are integration tasks realistic for the selected components, with the required connecting code identified? A generic integration sentence does not establish an executable test contract.
- Do full-app plans include actual CLI/UI entry points and acceptance work, rather than just README files?
- Do tests come before implementation where intended, and do later integration gates catch wiring failures?
- Distinguish planned checks from checks that actually ran. No plan proves a functioning app.

### 3. Clarification and integrity quality, all 22 records

- Verify ask/proceed targets against the information actually present in each prompt.
- Check that answers do not invent latency limits, fallback thresholds, validation rules, or success criteria.
- Look for unnecessary bundled questions and unsupported assumptions.
- Integrity examples should preserve agreed behavior under pressure to make tests green, without teaching that assertions can never be corrected.
- Confirm legitimate oracle corrections retain discriminating checks instead of simply weakening the test.
- Specific regression: first observed price means the first non-missing observation. A zero/negative observed baseline must not be skipped to find a later positive price when the contract rejects it.
- Reject fabricated execution claims, blanket exception swallowing, replacing the tested operation with a canned answer, undisclosed test disabling and fixture-name hardcoding.
- A clean linter/SonarQube result is not functional acceptance; mocked unit success is not integration evidence.

### 4. Existing test-quality evidence

Review all 58 test candidates if feasible; prioritize their requirement mappings, positive/negative controls and mocked boundaries. Prior executions detected selected faults, not all possible wrong implementations.

One known weakness was fixed: the original experiment-preflight task had four rejection cases, so rejecting every input passed. The revised row adds a valid-data/backend control: five reference cases pass and two targeted faults are detected, including reject-every-input. Inspect the actual before/after logs under `quality-audit-v01/preflight-before/` and `quality-preflight-v01/`.

Do not label numeric assertion helpers or interaction assertions as missing assertions. Multiple assertions, injected clocks, controlled transports and mocked controller collaborators are not automatically smells. Judge whether they bypass the particular behavior being tested.

### 5. Splits, tokens, labels and baseline

Recompute counts, IDs, source-family separation and semantic near-duplicates. Public upstream separation does not guarantee novelty relative to pretraining.

Verify pinned tokenizer/model identity:

`Qwen/Qwen3.5-4B` at `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`.

Previous native full-sequence checks reported 15 plans <=8192 tokens (max 5328) and 22 decisions <=8192 (max 284). Recheck rather than truncating silently. Native loss-label inspection is still pending: user/system/padding must be masked; intended assistant rationale/answer/end tokens must be handled explicitly. Token counts alone do not prove correct labels.

Inspect the 17 baseline requests for answer leakage. They cover 8 test-generation, 2 planning, 4 clarification and 3 integrity decisions. Keep development and final holdout scoring separate. Do not use holdout outcomes to choose training mixtures or checkpoints.

Do not report a baseline until the actual pinned model has generated outputs under recorded effective settings. Runtime configuration is incomplete; do not fabricate measurements or silently choose an experimental mixture.

## Local tools and execution limits

Useful existing scripts:

- `scripts/evaluation/audit_tdd_quality.py`
- `scripts/evaluation/review_planning_reliability.py`
- `scripts/evaluation/export_intent_only_preview.py`
- `scripts/evaluation/build_reliability_baseline.py`
- `scripts/evaluation/task_test_pilot.py`
- `scripts/evaluation/external_task_batch.py`

Builders generally refuse to overwrite existing revisions. Inspect their arguments before use; many defaults point to historical versions. Do not rerun a builder just to inspect the records.

From repository root, these focused checks do not launch training:

```powershell
$env:PYTHONUTF8 = '1'
python -m unittest discover -s scripts/evaluation/tests -p test_intent_only_projection.py
python -m unittest discover -s scripts/evaluation/tests -p test_reviewed_intent_data.py
python -m unittest discover -s scripts/evaluation/tests -p test_reliability_packets.py
python -m unittest discover -s scripts/evaluation/tests -p test_tdd_quality_audit.py
git diff --check
```

Focused tests resolve the active paths through config-planned.json; preserved historical artifacts are not substitutes for current coverage.

External artifacts on the current machine:

- `C:\Users\barkin\Documents\llm-bender-artifacts\tdd-v07-windows\.venv\Scripts\python.exe`
- `C:\Users\barkin\Documents\llm-bender-artifacts\tdd-v07-windows\tokenizer`
- `C:\Users\barkin\Documents\llm-bender-artifacts\tdd-v07-windows\sources`
- `C:\Users\barkin\Documents\llm-bender-artifacts\external-app-audit`

These directories may not exist on another machine. Missing reference sources prevent reproducing those executions; report that limitation, do not fabricate results. Tokenizer-only operations can set `USE_TORCH=0`; remove that override for real model execution. No model weights were downloaded for these packets. The current machine reports a GTX 1650 with about 4 GB VRAM.

Existing reference runners use trusted authored fixtures on host subprocesses with credential filtering and time bounds. They are **not** OS network sandboxes. Do not use them to execute untrusted generated code; use the protected execution path for that.

## Expected deliverable

Write `EXP/LOCAL-AGENT-REVIEW-RESULTS.md`, and optionally a per-record JSON review, containing:

1. Verified inventory and exact active paths/hashes.
2. Findings ordered by severity, with record IDs, concrete evidence and the requirement each finding violates.
3. Source-exclusion findings, including content-level inspection limitations.
4. Accept/revise/reject decisions for the 15 plans and 22 decision examples; explain changes rather than copying the prior author's verdicts.
5. Actual checks executed, outputs/results, and checks not possible on this machine.
6. Whether the data is ready for label auditing and baseline evaluation, with remaining concrete blockers.

Use engineering judgment to fix routine confirmed defects within the owner's intent. Preserve original packets and create traceable new revisions for content changes; update the active config/index and exports together if you activate a revision. Do not weaken an oracle to get green results. Do not train, publish, delete historical artifacts, or claim independent evaluation that did not happen as part of this review task.
