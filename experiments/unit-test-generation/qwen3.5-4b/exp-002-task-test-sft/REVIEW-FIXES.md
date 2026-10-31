> Native-label audit now passes for the active 78-candidate projection. See [NATIVE-LABEL-AUDIT.md](NATIVE-LABEL-AUDIT.md) for actual masks, token counts and scope. Trainer parity, semantic overlap review and runtime baseline remain pending. Older pending-audit statements below describe prior state.

# Independent-review fixes

The original independent report `LOCAL-AGENT-REVIEW-RESULTS.md` is preserved unchanged. This follow-up records fixes and actual verification, not a replacement review or model evaluation.

## Finding A: shared-file task ordering

Confirmed the blocker: 13 of 15 v03 plans had unordered tasks editing shared files. The new `planning-pilot-v04` preserves existing logical prerequisites, uses a stable topological order, and adds 34 explicit resource-order dependency edges. All shared-file writer pairs now have an ancestor relationship; independent-file tasks remain eligible for parallel work. Resource ordering is labeled separately from user requirements.

The reviewer-authored `.review-scratch/check_shared_file_serialization.py` was executed against the original v03 bundle and against v04, changing only the input path in memory. It reports 13 conflicted plans before and zero after (all 15 v04 plans pass). Original script and v03 data were not edited. Outputs and the script hash are stored under `review-fixes-v01`.

The revision includes synchronized records, review text, content-review evidence and materialized child prompts with matching prerequisite lists. `intent-only-preview-v02` regenerates the 13 planning training targets. `baseline-reliability-v03` regenerates the held-out planning requests/references. All 15 native sequences fit 8192 tokens; maximum 5328. No truncation occurred.

## Finding B: stale regression coverage

Focused data tests now resolve active planning, reliability, baseline, preview and test-selection paths through `active_tdd_data.py` and `config-planned.json`. They check current request isolation, action coverage, projection content, child dependencies and active target/reference synchronization. Added tests also cover sibling conflicts, reverse list ordering, transitive prerequisites, normalized paths, cycles/unknown dependencies and preserving independent tasks.

## Finding C: inventory ambiguity

The nine-entry `training_source_families` list was correct for training. Posting is development and ddgr is holdout; adding them to the training-family list would misrepresent the split. The config now separately records all 11 `source_families` and `source_families_by_split`. A regression check verifies the inventory against all three active tracks and keeps evaluation families out of the training list.

## Finding D: provisional price policy

The crypto plan now explicitly marks its adjusted-close/provider adapter details as provisional, contingent on resolving `price-definition`. The same text is included in the relevant materialized child contracts. The existing task-to-test contracts and reference tests were not changed; this correction concerns the earlier planning-stage distinction between proposed policy and agreed behavior.

## Finding E: auditor omitted the active replacement

`candidate-index-v03.json` identifies the same active 58 test rows with their materialized path/hash. `audit_tdd_quality.py` now resolves this active selection rather than the two historical source bundles. Its new `quality-audit-v02/static-test-triage.json` includes the corrected preflight row and excludes the superseded row. It scans 58 rows and reports zero current heuristic flags. This is mechanical triage, not proof of complete semantic correctness.

## Verification

- 18 focused unittest checks pass across projection, reviewed data, reliability packets, quality triage and file serialization.
- Independent review checker: 13/15 conflicted plans before; 0/15 after.
- Active planning conversations: all <=8192 native tokens, maximum 5328.
- Preview count remains 78: 50 tests, 13 plans, 15 decisions. Export allowlist and evaluation exclusion checks pass; source implementation remains audit-only.
- Overall collection count remains 95: 58 tests, 15 plans, 22 decisions. No example-count inflation.
- New baseline packet remains 17 requests, with grader targets separate and no model inference performed.
- `git diff --check` passes.

## Current state and remaining work

The confirmed planning contradiction and active-data tooling gaps are fixed. The original report's broad source-exclusion/decision findings remain useful evidence, but this follow-up does not claim another independent content review of every regenerated message. Changes add scheduling and provisional-policy text, not repository implementation bodies.

Native loss-label auditing, final source-text checks for the serialized revision, semantic near-duplicate review, experiment mixture selection and runtime/protocol configuration remain pending. Semantic near-duplicate review can include direct cross-family inspection; embedding tooling is optional, not a prerequisite for doing that review. No training or starting-model inference has run, and baseline readiness is not claimed merely because these fixes pass.

Active config references: planning-pilot-v04, reliability-pilot-v03, intent-only-preview-v02, baseline-reliability-v03 and candidate-index-v03.json. Earlier artifacts remain preserved.
