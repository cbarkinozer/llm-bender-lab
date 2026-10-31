> Native-label audit now passes for the active 78-candidate projection. See [NATIVE-LABEL-AUDIT.md](NATIVE-LABEL-AUDIT.md) for actual masks, token counts and scope. Trainer parity, semantic overlap review and runtime baseline remain pending. Older pending-audit statements below describe prior state.

> Active review fixes: [REVIEW-FIXES.md](REVIEW-FIXES.md). Planning v04 fixes shared-file ordering; current preview is intent-only-preview-v02 and baseline packet is baseline-reliability-v03. Counts are unchanged. Older revision descriptions below are preserved history.

# Content review and intent-only data policy

The active collections remain **58 test-generation, 15 planning and 22 clarification/integrity examples: 95 total, 78 train-family candidates**. No training is enabled and no model capability has been measured.

## User-defined boundary

The learning workflow is user intent -> necessary clarification -> divide-and-conquer plan -> file-level task -> requirement-based pytest tests. Repository implementation source must never appear in model input or training targets. Source/reference columns may be retained for audit and reference execution but must be excluded from training serialization. Public interface signatures and behavioral contracts are allowed as explicit task context or clearly proposed planning choices. Pytest targets and necessary synthetic fixture snippets remain task content.

`intent-only-preview-v01` enforces a field allowlist: each training record contains only `messages`; each message contains role/content, with optional assistant reasoning_content. It excludes source columns, reference implementations, mutation code, validation logs and grading references. Separate audit-index.json tracks provenance without entering model-visible records. A regression fixture injects source/reference sentinels at top level and inside message metadata; none survive the projection. Development/holdout rows are rejected.

The allowlist prevents accidental column leakage, but cannot automatically establish that arbitrary text inside content is not an implementation solution. A final review of serialized messages and native loss labels remains required before enabling training. Never stringify the entire rich record or automatically concatenate source/audit columns into a prompt. This preview is a review artifact, not an approved mixed training recipe.

## Review outcome

All 37 planning/decision drafts received an assistant content review in this workspace; no outside judge or human reviewer is claimed.

- Planning: 15 revised. Existing task inventories did not adequately distinguish inferred APIs from user requirements, several full-app delivery tasks listed only documentation files, and integration was often a general instruction instead of an executable todo. Revised targets label internal interfaces as proposals, include targeted behavior questions, preserve autonomous routine design choices, add concrete integration tasks, and identify actual entry-point files for full-app delivery. Scoped variants retain their limited scope. All task graphs resolve without cycles; every plan has an integration task and materialized child inputs with the required context. These are plans, not implemented integration tests.
- Decisions: 14 retained and 8 revised. Revisions remove an unagreed nonpositive-baseline assumption, preserve the no-secrets intent while clarifying its scope, replace ambiguous pseudo-values with exact string pairs, make the mocked call explicit, and add missing orchestration/equivalence/disabled-row requirements to the prompts that rely on them. The first-observed-price correction now explicitly forbids skipping an invalid observed baseline to find a later positive one.
- No extra rows were added by these revisions. Original v02 collections and per-record hashes are preserved through review_lineage and content-review.json. The new active collections are planning-pilot-v03 and reliability-pilot-v03.

The reviewer is also the author/editor; this is not independent validation. Structural checks and content review do not prove learning, app correctness, task coverage in every interpretation, or resistance to cheating.

## Validation and current artifacts

- All 15 reviewed plan conversations fit the 8192-token limit; maximum 5091.
- All 22 reviewed decision conversations fit; maximum 284.
- Five new regression tests pass: source-column exclusion, heldout rejection, proposal/integration fields, the first-observed baseline correction, and the 78-record projection count/shape.
- Existing 58 test candidates and their corrected preflight selection remain unchanged.
- baseline-reliability-v02 refreshes the 17 evaluation requests to the reviewed drafts. Model-facing requests still omit targets; reference answers remain separate. Decoding/backend settings are not frozen and inference has not run.

Review files:

- [15 reviewed plans](planning-pilot-v03/review-examples.txt)
- [22 reviewed decisions](reliability-pilot-v03/review-examples.txt)
- [Intent-only export policy and counts](intent-only-preview-v01/manifest.json)
- [Updated model-facing baseline requests](baseline-reliability-v02/requests-for-model.txt)

Next: inspect actual native labels and the final model-visible text, select which capability mixture to test, then freeze and run the starting-model baseline on a configured runtime. Keep the first test-only hypothesis distinct from a planning/reliability mixture. No implementation/source-to-test training track is authorized by these datasets.
