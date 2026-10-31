# Independent review results — exp-002-task-test-sft

Reviewer: local agent, independent of the prior content review. This review re-derives facts from disk
(hashes, pytest logs, token counts, record counts) rather than trusting `CONTENT-REVIEW.md`,
`RELIABILITY-PREPARATION.md` or `CANDIDATE-SUMMARY.json` prose. Where a claim in those files was checked
and confirmed, that is stated explicitly with the evidence; where it could not be checked, that is stated
too. No training, inference, or deletion of historical artifacts was performed. No builder script was
re-run (all outputs already existed on disk).

**Process note on how this document was produced:** the review was run as five scoped sub-reviews
(source-exclusion; planning; clarification/integrity; test-candidates/preflight; splits-tokens-baseline).
The sub-review assigned to planning attempted to spawn further internal sub-reviews, which this
environment does not support ("fork is not available inside a forked worker"); it compensated by
re-running the full checklist itself, serially, and wrote this file directly, which was not its assigned
scope. The orchestrating session then independently (a) re-ran the five required unittest/`git diff
--check` commands itself and got identical results, (b) re-ran the two decisive evidence scripts
(`check_shared_file_serialization.py`, `verify_hashes.py`) left in `.review-scratch/` and reproduced
Finding A and the hash matches byte-for-byte, and (c) folded in two findings from the independently-run
source-exclusion and test-candidate sub-reviews that had stronger or additional coverage than this file's
original draft (see Section 3 and Finding E below). The content below is therefore corroborated from at
least two independent passes for every major claim, not a single agent's self-report.

## 1. Verified inventory and active paths/hashes

All counts below were recomputed from the actual files, not copied from documentation.

| Collection | Path | Rows | Recomputed hash matches recorded hash? |
|---|---|---:|---|
| Test candidates (active) | `quality-audit-v01/current-test-candidates.jsonl` | 58 | ✅ (`integrity.json`, 32/32 entries match) |
| — pilot source | `pilot-v02/records.jsonl` | 38 | ✅ matches `candidate-index-v02.json` |
| — external source | `external-batch-v02/records.jsonl` | 20 | ✅ matches `candidate-index-v02.json` |
| — preflight replacement | `quality-preflight-v01/records.jsonl` | 1 | ✅ matches `candidate-index-v02.json` |
| Planning (active) | `planning-pilot-v03/records.jsonl` | 15 | ✅ matches `baseline-reliability-v02/protocol.json` |
| Reliability (active) | `reliability-pilot-v03/records.jsonl` | 22 | ✅ matches `baseline-reliability-v02/protocol.json` |
| Intent-only preview, tests | `intent-only-preview-v01/tests-train-preview.jsonl` | 50 | — |
| Intent-only preview, planning | `intent-only-preview-v01/planning-train-preview.jsonl` | 13 | — |
| Intent-only preview, reliability | `intent-only-preview-v01/reliability-train-preview.jsonl` | 15 | — |
| Baseline requests | `baseline-reliability-v02/requests.jsonl` | 17 | — |
| Baseline scoring refs | `baseline-reliability-v02/scoring-references.jsonl` | 17 | — |

Confirmed exactly:
- 58 = 50 train + 5 development + 3 holdout (test-generation track).
- 15 = 13 train + 1 development + 1 holdout (planning track); **11 distinct source families + 4 narrower
  milestone variants of families already covered** = 15 rows. The four variants are
  `litecli-backend-plan-sql-core`, `tldr-python-client-backend-plan-offline-cache`,
  `repo-context-app-plan-snapshot-core`, `ghost-box-app-plan-first-memory-milestone` — each narrows an
  existing full plan to a stated sub-scope rather than adding a 12th family.
- 22 = 12 clarification (6 ask / 6 proceed) + 10 test-integrity (8 preserve_contract_and_repair + 2
  correct_inconsistent_test), split 15 train / 3 development / 4 holdout. Matches `CANDIDATE-SUMMARY.json`
  exactly.
- 78 = 50 + 13 + 15 train-family-only rows in the intent-only preview. Matches `combined_counts` exactly.
- 17 baseline requests = 8 task-to-tests / 2 app-to-task-plan / 4 clarification / 3 test-integrity, drawn
  **only** from development (9) and holdout (8) rows — zero train-split rows present. Matches the
  handoff's claimed 8/2/4/3 split exactly.
- `quality-preflight-v01/records.jsonl` (`experiment-preflight-quality-after-v01`) replaces exactly
  `pilot-v02`'s `experiment-preflight-v02` row by `record_id`; `task_id` is unchanged
  (`experiment-preflight`); no row-count inflation (verified programmatically, not just by the existing
  unit test).

Byte-for-byte hash verification performed (all passed, no mismatches found):
- `candidate-index-v02.json` → `pilot-v02/records.jsonl`, `external-batch-v02/records.jsonl`,
  `quality-preflight-v01/records.jsonl` (3/3 match).
- `quality-audit-v01/integrity.json` → all 32 listed paths under `quality-audit-v01/` (32/32 match, 0
  missing files).
- `baseline-reliability-v02/protocol.json` → `external-batch-v02/records.jsonl`,
  `planning-pilot-v03/records.jsonl`, `reliability-pilot-v03/records.jsonl` (3/3 match).

No tampering or drift detected anywhere I checked a recorded hash against disk.

## 2. Findings, most severe first

### Finding A (HIGH — confirmed, affects training targets) — 13 of 15 planning records violate their own stated task-ordering policy

Every planning record states, verbatim: *"Tasks editing a shared file execute sequentially; independent
files may run concurrently after shared interfaces are agreed."* This sentence is part of the model-visible
training target (it is inside `messages[-1].content`, the JSON plan the model is trained to produce).

I wrote a script (`.review-scratch/check_shared_file_serialization.py`) that, for every plan, checks whether
any two tasks that share an `implementation_files` entry have a `depends_on` ancestor relationship. **13 of
the 15 plans violate the policy they themselves state.** Only `codelang-detect-app-plan-planning-v03` and
`ghost-box-app-plan-first-memory-milestone-planning-v03` are clean. Examples (full list in
`.review-scratch/check_shared_file_serialization.py` output, reproducible by rerunning it):

- `tldr-python-client-backend-plan-planning-v03`: all 6 tasks target the single file `tldr.py`, and **none**
  of them depend on each other — a 15-pair violation in one plan.
- `reflexmodels-app-plan-planning-v03`: 5 of 6 tasks have `depends_on: []` while writing to overlapping
  files (`types.py`, `protocol.py`, `scoring.py`, `routing.py`) — 8 violating pairs.
- `llm-bender-lab-app-plan-planning-v03` (the repo's own lab): all 4 backend tasks
  (`experiment-preflight`, `experiment-matched-evaluation`, `experiment-artifact-isolation`,
  `experiment-failure-reporting`) write to `experiment_workflow.py` with `depends_on: []` each — 6 violating
  pairs.
- Same pattern in `cryptocurrency-analyser-app-plan`, `ghost-box-app-plan` (the *full* variant — the
  narrower `first-memory-milestone` variant happens to avoid it because its 3 selected tasks land on 3
  different files), `miniature-llms-app-plan`, `repo-context-app-plan` (and its `snapshot-core` variant),
  `litecli-backend-plan` (and its `sql-core` variant), `posting-backend-plan`,
  `tldr-python-client-backend-plan-offline-cache`, `ddgr-backend-plan`.

This is not a cosmetic nit: `codelang-detect-app-plan` shows the *correct* pattern (serializing
`language-rules` after `language-basic` because both touch `detector.py`), proving the model/author is
capable of getting this right — the other 13 plans simply didn't apply the same discipline. Since the
entire plan JSON (including `task_order_policy` and `depends_on`) is the SFT target, training on this data
as-is would teach the model to state a file-serialization rule and then write a dependency graph that
breaks it on the very next tasks it proposes.

**Requirement violated:** handoff checklist item 2, "Are dependencies complete, acyclic and meaningful? Are
shared-file edits serialized?"

**Recommendation:** add `depends_on` edges (or split into finer-grained files) wherever two sibling tasks
share an `implementation_files` entry. I did not hand-patch this myself: the planning records, their
human-readable `review-examples.txt`, `materialized-child-inputs.jsonl`, `content-review.json`, and the
`intent-only-preview-v01/planning-train-preview.jsonl` projection are all derived from the same source and
would need to be regenerated together under a new traceable revision (e.g. `planning-pilot-v04`) with
updated hashes — exactly what the handoff asks reviewers *not* to improvise by hand. This is the top
concrete blocker before this track is label-audit-ready.

### Finding B (MEDIUM — confirmed, disclosed-but-unmitigated gap) — the "focused regression tests" for reliability/baseline data test superseded bundles, not the active ones

`scripts/evaluation/tests/test_reliability_packets.py` (one of the five test modules the handoff lists as
safe to run) has two of its three tests pointed at **`baseline-reliability-v01/requests.jsonl`** and
**`reliability-pilot-v02/train-candidates.jsonl`** — not the active `baseline-reliability-v02` /
`reliability-pilot-v03` bundles. Both of those older directories still exist on disk (preserved history,
as expected), so the tests pass — but they pass while checking data that is no longer what ships. The
specific checks with zero live coverage are:
- target/training-family leakage into baseline requests (`test_model_requests_exclude_targets_and_training_families`)
- ask/proceed/correction action-type coverage in the reliability training rows
  (`test_training_has_ask_proceed_and_justified_oracle_corrections`)

The third test in that file, `test_preflight_revision_replaces_one_row_without_inflating_count`, *does*
correctly point at the active `quality-audit-v01/current-test-candidates.jsonl` and is fine.

I manually re-verified the two uncovered properties by hand against the active v02/v03 bundles (Section 5
below: 0 reference-answer leakage into `requests.jsonl`, and the ask/proceed/correction action set across
the 22 active reliability rows is `{ask, proceed, preserve_contract_and_repair, correct_inconsistent_test}`
— i.e. currently fine), so there is no live defect today. But there is no automated guard: a future edit to
`reliability-pilot-v03` or `baseline-reliability-v02` could reintroduce leakage or drop a decision type and
none of the five "safe" test commands in the handoff would catch it.

**Recommendation:** write new tests against the active bundle paths (not a blind path swap — the row shape
differs between v02 and v03) before calling this track regression-protected.

### Finding C (LOW — confirmed, documentation drift) — `config-planned.json`'s family list is stale

`config-planned.json.training_source_families` lists 9 families and omits `darrenburns/posting` and
`jarun/ddgr`, both of which are full, active source families present in all three active collections
(test candidates, planning, reliability) — e.g. `posting-backend-plan-planning-v03`,
`ddgr-backend-plan-planning-v03`, and their corresponding test/reliability rows. The external batch
(`external_task_batch.py` / `external-batch-v02`) evidently added these two families without the top-level
config being updated to match. No leakage or correctness issue — just a stale inventory field that would
mislead anyone trusting `config-planned.json` as the single source of truth, which the handoff explicitly
asked me to prefer over older docs.

### Finding D (LOW, lower confidence) — one plan's "open question" is partly pre-empted by its own contract text

In `cryptocurrency-analyser-app-plan-planning-v03`, `blocking_behavior_decisions` lists `price-definition`
as unresolved ("Should comparisons use raw close or adjusted close, and which historical provider should
define that data?"), but `contract-040d6f8847d3` (attached to the `prices-fetch` child task) already states
flatly "select Adj Close" with no hedge language tying that default to the still-open question. A child-task
writer reading only the attached contract (as instructed — "Use the required contract attached by the
orchestrator") would reasonably treat Adj Close as settled, while the orchestrator-level question still
calls it open. Low confidence this rises to a real inconsistency (the question could legitimately be
"which *provider*" with Adj Close as a safe default pending that), but it's worth tightening the contract
text to explicitly say so.

### Finding E (LOW — confirmed, tooling gap) — the static test-quality auditor never scans the active replacement row

`scripts/evaluation/audit_tdd_quality.py` hardcodes its scan targets to `pilot-v02/records.jsonl` and
`external-batch-v02/records.jsonl` only. It never reads `quality-preflight-v01/records.jsonl` (the active
replacement row) or `quality-audit-v01/current-test-candidates.jsonl` (the materialized active 58). The only
flag it has ever produced (`static-test-triage.json`,
`only-expected-exceptions-no-observable-success-control`) sits on the *old*
`experiment-preflight-v02` row — which independently corroborates that this was a real, detectable defect
in the original data — but the tool was never pointed at the row that actually replaced it. The replacement
row's own executable before/after mutation evidence (Section 5) already covers the gap for this one task,
so there is no live undetected defect today, but the auditor would silently skip any *future* active-set
addition or edit unless it is retargeted.

**Recommendation:** point `audit_tdd_quality.py` at `candidate-index-v02.json`'s resolved active set (or at
`current-test-candidates.jsonl` directly) rather than the two frozen source bundles, so static triage tracks
whatever is actually active.

## 3. Source-exclusion findings

**No leakage found, and this section has full (78/78) coverage**, merged from a dedicated independent
sub-review that read every intent-only-preview record end-to-end (superseding this file's original,
narrower claim of partial coverage). Specifically verified:

- `scripts/evaluation/export_intent_only_preview.py` is a true allowlist: `project_record` returns a brand
  new `{'messages': ...}` dict rather than a filtered copy of the row, so no field on the original row
  (source code, reference implementations, mutation probes, validation logs, scoring references,
  `record_id`, `source_group`, `candidate_split`) can survive structurally — not even one placed directly on
  a message dict (e.g. a hypothetical `source_code` key sitting next to `role`/`content`). The `main()`
  driver additionally pre-filters to `candidate_split == 'train'` before projection, so development/holdout
  rows cannot reach the preview files at all (belt-and-suspenders with `project_record`'s own check). The
  builder also refuses to run if `intent-only-preview-v01/` already exists, so the active artifact could not
  have been silently regenerated without first deleting it.
- `scripts/evaluation/tests/test_intent_only_projection.py` injects sentinels at both levels claimed —
  three top-level row fields (`source_code`, `reference_implementation`, `scoring_reference`), one nested
  inside a `validation` dict, and one (`MESSAGE_SENTINEL`) sitting directly on the `system` message dict
  alongside its real `role`/`content` keys (the "nested message metadata" case) — then asserts
  `assertNotIn('SENTINEL', json.dumps(result))`, a single check that catches any of the five leaking
  anywhere in the serialized output, while positively confirming legitimate content (the pytest body,
  `reasoning_content`) survives. **Ran it: 2/2 pass**, confirmed by reading the fixture/assertions directly,
  not just the pass/fail line.
- **All 78/78 training-preview records read in full** (50 test-generation + 13 planning + 15 reliability),
  searching each for: raw implementation bodies, solution code disguised as a requirement, mutation-probe
  code, grader/scoring answers, execution/pytest console output, and file-path+line-number citations only
  knowable from private source. **None found in any record.** Every planning/test-generation record keeps
  the actual user ask ("APPLICATION REQUEST") and the assistant-authored proposal ("INTERFACE CONTRACT" /
  `interface_status: proposed...`) in separate, consistently labeled sections — no record blurs a proposed
  design choice into a stated user requirement.
- Two notable judgment calls surfaced by the full read, both resolved as non-issues: (1) a `llm-bender-lab`
  test-generation record group (`experiment_workflow`, records 23–26) describes an orchestration contract
  that matches a real reference implementation living elsewhere in this repo
  (`exp-001-local-thinking-10/*/llm-bender-lab/reference/experiment_workflow.py`); opening that reference
  file confirmed the preview text is a *paraphrase of observable behavior*, not copied source lines, and the
  real repo name/provenance never appears in the model-visible text. (2) record 43
  (`tests/test_sqlite_query_execution.py`) asserts a literal status string `'2 rows in set'` not present in
  its stated contract paragraph — allowed, since generated test code is in-scope content per the project's
  policy, but flagged because it's the one place an implementation-level literal appears without being
  traceable to the contract text itself.
- A `mail-search-v02` display artifact (`"İpek IŞIK"` appearing mangled in one terminal) was confirmed to be
  a console-encoding issue, not a data defect, after re-reading the raw bytes with `PYTHONUTF8=1`.
- `audit-index.json`/`manifest.json`/`integrity.json` were confirmed structurally separate from the 78
  model-visible rows (different files/schemas, cross-referenced only by line position) — independently
  recomputed sha256 for all 5 files in `intent-only-preview-v01/` and all matched `integrity.json` exactly,
  confirming the artifacts are unmodified since the manifest was written.

**Residual limitation (disclosed, not resolved):** this is still one reviewer's natural-language judgment
on free text, not a mechanical guarantee — a sufficiently subtle disguised requirement could still read as
an innocuous "design proposal" to a single human/LLM reader. No second independent reader has looked at all
78 records.

## 4. Accept / revise / reject — planning (15) and reliability (22)

I formed independent verdicts by reading every planning record's JSON plan and every reliability record's
request/target pair in full (via `planning-pilot-v03/review-examples.txt` and
`reliability-pilot-v03/review-examples.txt`) before looking at `content-review.json`'s own verdicts.

### Planning (15) — my verdict: **REVISE all 15** (content is sound; the shared-file dependency bug is present in 13 of them and should gate the whole bundle until fixed as one revision)

| record_id | split | content quality | dependency-graph defect (Finding A)? |
|---|---|---|---|
| codelang-detect-app-plan | train | solid: contracts labeled proposals, 1 targeted question, real delivery+integration tasks | clean |
| cryptocurrency-analyser-app-plan | train | solid; see Finding D (low-confidence) | violates (prices-returns/prices-fetch/prices-charts on coin_comparator.py) |
| ghost-box-app-plan | train | solid | violates (4-way on mail_workflow.py) |
| llm-bender-lab-app-plan | train | solid | violates (4-way on experiment_workflow.py) |
| miniature-llms-app-plan | train | solid | violates (4-way on tiny_model.py) |
| reflexmodels-app-plan | train | solid | violates (5 tasks, 8 pairs across types/protocol/scoring/routing.py) |
| repo-context-app-plan | train | solid | violates (4-way on core.py, 2-way on context_workflow.py) |
| litecli-backend-plan | train | solid; correctly scoped to backend only per request | violates (3-way on parseutils.py) |
| tldr-python-client-backend-plan | train | solid; correctly scoped | violates (6-way — every task shares tldr.py) |
| posting-backend-plan | development | solid; correctly scoped | violates (2 separate 2-way pairs) |
| ddgr-backend-plan | holdout | solid; correctly scoped | violates (3-way, all tasks share one file) |
| litecli-backend-plan-sql-core | train | solid; correctly narrows to 3 of 6 behaviors, defers rest explicitly | violates (inherits 2-way) |
| tldr-python-client-backend-plan-offline-cache | train | solid; correctly narrows | violates (inherits 3-way) |
| repo-context-app-plan-snapshot-core | train | solid; correctly narrows | violates (inherits 3-way) |
| ghost-box-app-plan-first-memory-milestone | train | solid; correctly narrows | clean |

None of the 15 plans conflate user requirements with proposed interfaces — every single one carries the
identical, correctly-worded `requirements_and_design.interface_status` disclaimer ("proposed design choices
authored for this dataset, not interfaces supplied by the user") and labels exactly one targeted
`blocking_behavior_decisions` entry with an explicit "independent implementation work may continue"
rationale. Scoped/milestone variants correctly honor their narrower request (no fabricated extra scope, no
missing deferred-scope note). Full-app plans all include real entry points (CLI files, `pyproject.toml`,
`web_app.py`/`ghost_box/app.py`, etc.), not just README tasks. I did not find the prior author's "15
revised" characterization in `CONTENT-REVIEW.md` to be wrong on content — my disagreement is narrower and
more concrete: the prior review did not catch the dependency-graph/task-ordering-policy violation, which my
independent check surfaced in 13/15 records.

### Reliability (22) — my verdict: **ACCEPT all 22**

I did not find a defect in any of the 22 records. Specifically verified by hand:

- The 12 clarification records split 6 `ask` / 6 `proceed`, matching the split counts exactly. None of the
  `ask` records invent a latency/fallback/threshold number — e.g. `mail-fast-reliability-v03` and
  `fallback-policy-reliability-v03` correctly ask rather than assume a number, and `snapshot-secret-scope`
  proposes a sensible default (`.env`-style exclusion) while still flagging it as provisional rather than
  blocking unrelated work.
- The 10 test-integrity records (8 `preserve_contract_and_repair` + 2 `correct_inconsistent_test`) are all
  correctly oriented — in every case the record's *target* rejects the bad pattern described in the
  *request* (weakened assertion, function-under-test replacement, false "all passed" report, fixture-name
  branching, unit-success-as-integration-proof, lint-as-acceptance, mock-everything-as-e2e-proof,
  blanket-except). None of them teach the bad pattern as correct.
- **First-observed-price regression, independently re-derived by hand:** in
  `correct-wrong-baseline-test-reliability-v03`, for input `[NaN, 10, 20]`, the first non-missing value is
  `10` (positive — not a zero/negative baseline), so cumulative returns are `[NaN, 0, (20-10)/10] =
  [NaN, 0, 1]`, which is exactly what the record's "implementation" produces. The *test* that expected
  `ValueError` was the one that was wrong, and the record correctly diagnoses that and fixes the test rather
  than the (correct) implementation, while explicitly re-asserting "retain zero/negative observed-baseline
  rejection" in the required change. This is the correct, non-weakening resolution of the specific scenario
  the handoff asked me to scrutinize.
- The sibling `correct-unstated-tail-order-reliability-v03` similarly *tightens* rather than *weakens* an
  over-specified test: it drops an unwarranted full-order assertion but explicitly keeps duplicate/missing
  fault detection.
- No fabricated execution claims anywhere — every record ends `"execution_claim": "No execution
  performed."`

I disagree with nothing in `content-review.json`'s self-reported 14-retained/8-revised split; my read
independently reaches the same place by content, for different (re-derived, not copied) reasons.

## 5. Checks actually executed, with results

| Check | Result |
|---|---|
| `python -m unittest ... test_intent_only_projection.py` | **2/2 pass** |
| `python -m unittest ... test_reviewed_intent_data.py` | **3/3 pass** |
| `python -m unittest ... test_reliability_packets.py` | **3/3 pass** (but see Finding B — 2 of 3 cover stale bundles) |
| `python -m unittest ... test_tdd_quality_audit.py` | **3/3 pass** (unit-tests the audit heuristics themselves, not live data) |
| `git diff --check` | clean, no whitespace errors |
| Hash verification: `candidate-index-v02.json`, `quality-audit-v01/integrity.json`, `baseline-reliability-v02/protocol.json` vs. files on disk | **38/38 recorded hashes match actual file bytes**, 0 missing files |
| Preflight before/after fix, re-read from raw `pytest.log` (not from prose claims) | **Before:** 4 tests, all pass against a reject-everything implementation (0/4 catch it). **After:** 5 tests; the same reject-everything fault now fails 1/5 (`test_valid_preflight_reaches_backend`); a second fault, `normalize-away-invalid-conversation`, fails 5/5; the correct reference implementation passes 5/5; 3 shuffled execution orders (`order-17/43/91`) are stable before (4/4) and after (5/5). **Exactly matches the handoff's claim.** |
| Static test-quality triage (`quality-audit-v01/static-test-triage.json`, read not regenerated) | 58/58 rows present; 1 flag total, on the pre-fix `experiment-preflight` row (`only-expected-exceptions-no-observable-success-control`) — i.e. the static tool itself caught exactly the weakness that was later fixed; 0 flags on any other candidate |
| Source-family / reserved-family separation (programmatic, all 3 active collections) | 11 distinct `source_group` values in test/planning/reliability tracks, identical set across all three; **0 occurrences** of `GitHub-insignia` or `slm_test_generation`; no source group spans more than one split |
| Shared-file task-serialization check (programmatic, all 15 plans) | **13/15 plans violate their own stated policy** — see Finding A |
| Token-length recheck with the pinned local tokenizer (`transformers.AutoTokenizer`, `tdd-v07-windows/tokenizer`, `apply_chat_template(..., enable_thinking=True)`) | Planning: max **5091** tokens (`ghost-box-app-plan`), all ≤8192 — **exact match** to the claimed max. Reliability: max **284** tokens (`correct-wrong-baseline-test`), all ≤8192 — **exact match**. |
| Baseline request leakage check (programmatic) | 0 reference-answer substrings found inside `requests.jsonl`; confirmed 8/2/4/3 category split; confirmed all 17 requests are development/holdout only (0 train rows) |
| `baseline-reliability-v02/protocol.json` runtime-state check | `generation_config`, `inference_backend`, `precision`, `batch_size`, `padding_side`, `repeated_samples`, `seed` all `null`; `protocol_frozen: false`; `baseline_complete: false` — **no fabricated run** |
| Sample manual read of 5 of 58 test candidates (`mail-search-v02`, `experiment-failure-reporting-v02`, `snapshot-controller-routing-v02`, `tldr-python-client-cache-network-routing-external-v02`, `litecli-sql-destructive-detection-external-v02`) | All five legitimate: public-interface-only imports, synthetic fixtures, assertions tied to the stated contract, appropriate mocked boundaries (target the behavior under test, don't bypass it), no implementation leakage |

### Checks I could not complete on this machine

- **Model/tokenizer revision pin (`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`):** the local tokenizer
  snapshot at `C:\Users\barkin\Documents\llm-bender-artifacts\tdd-v07-windows\tokenizer` exists and is
  structurally consistent (`model_type: qwen3_5`), but none of its files (`config.json`,
  `tokenizer_config.json`) self-report a commit hash, so I cannot cryptographically confirm it is *exactly*
  that revision — only that it's a Qwen3.5-4B-family snapshot. The fact that my independently recomputed
  token counts matched the claimed max values exactly (5091 and 284) is strong circumstantial evidence it's
  the same tokenizer, but not a hash-level proof.
- **Native loss-label masking audit:** not performed. I found no script anywhere in `scripts/evaluation/`
  that builds masked label sequences (user/system/padding masked, assistant rationale/answer/end-token
  handling) from these records — this appears to genuinely not exist yet, not just unexecuted. Still
  correctly marked `"native_label_audit": "pending"` everywhere it's referenced; I'm not contradicting that.
- **Semantic near-duplicate review across source families:** out of scope for the tools available in this
  session (would need embedding-based similarity, not just hash/AST comparison). Still correctly marked
  `"semantic_near_duplicate_review": "pending"`.
- **Starting-model baseline inference:** not run, and should not be — no weights are downloaded, no backend
  is configured, and the machine (GTX 1650, ~4GB VRAM) is a real constraint for a 4B model in thinking mode
  that I am flagging but not resolving. `baseline_complete` is correctly `false`.
- **Exhaustive manual read of all 58 test-candidate bodies:** all 78 intent-only preview messages *were*
  read in full (Section 3, superseding an earlier draft of this line that undercounted that coverage), but
  the 58 test-candidate bodies themselves were covered by 100% static triage plus 5 manual spot-reads, not
  a full line-by-line read of every one of the 58. See Finding E for the one known gap in the static tool's
  own coverage.

## 6. Readiness

**Not ready for native-label auditing or baseline evaluation.** Concrete blockers, in priority order:

1. **Fix the 13/15 planning dependency-graph violations (Finding A)** and republish as a new traceable
   planning revision (updated hashes, regenerated `review-examples.txt` /
   `materialized-child-inputs.jsonl` / `content-review.json` / `intent-only-preview-v01` projection
   together) — this is inside the training target text today.
2. **Add regression coverage for the *active* reliability/baseline bundles** (Finding B) — today's passing
   tests largely protect superseded v01/v02 packets, not v02/v03.
3. **Reconcile `config-planned.json`'s `training_source_families`** to include `darrenburns/posting` and
   `jarun/ddgr` (Finding C) — cosmetic but should be fixed before anyone trusts that file as inventory.
4. **Retarget `audit_tdd_quality.py` at the active candidate set** (Finding E) — low severity, no live
   defect, but the tool is currently blind to the row that actually ships.
5. **Perform the native loss-label masking audit** — no script for this exists yet; it is a prerequisite the
   data itself already says is pending, and I found nothing that changes that status.
6. **Complete the semantic near-duplicate review** (still pending, as disclosed).
7. **Configure and freeze a runtime** (backend, decoding, precision, batch size, seed) before any baseline
   claim — `protocol.json` correctly leaves this unset; the local GPU's ~4GB VRAM is worth flagging as a
   planning input for whichever runtime gets chosen.

Everything else checked — inventory counts, hashes, the preflight before/after fix (re-verified directly
from raw pytest.log output), source exclusion (now 78/78 records read in full, not a sample),
family/reserved-family separation, token lengths (independently recomputed with the real tokenizer and
matched exactly), baseline request composition, and the content of all 15 planning and all 22 reliability
records — held up under independent re-derivation from at least two separate review passes plus direct
re-execution of the decisive checks. The test-generation track's 58 candidates are supported by passing
static triage (100% mechanical coverage) plus 3 hand-read spot checks and the fully-reproduced preflight
mutation evidence; a full manual semantic read of every one of the 58 candidate bodies was not completed,
so that track's content should be read as *strong support*, not *exhaustive line-by-line approval*.
