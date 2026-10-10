# Paper pipeline reuse audit — 2026-10-10

Source checkout: `/Users/cbarkinozer/Documents/GitHub/slm_test_generation`.
Repository: https://github.com/Prof-it/slm_test_generation
Inspected commit: `380b7d362f49d43fd55af5b2f7e015d4fa651e97`.
The paper checkout was clean at inspection and remains unchanged.

## Decision

Reuse the paper's collection/extraction and oracle-analysis building blocks
through pinned adapters in this lab. Preserve the paper's frozen datasets,
generation outputs, design and analysis. Do not run its full build orchestrator
against the paper checkout: it writes canonical artifact paths.

General test-suite generation for correct functions/modules is the natural fit
for this pipeline. It remains distinct from SWT-style issue reproduction;
the owner's explicit task-mode decision is still pending.

## Reuse map

| Component | Existing code | New-experiment adaptation |
|---|---|---|
| Source discovery | `step2_data_preperation/collect_sources_v2.py` | Configurable dates and output root; fail on unresolved revisions; inspect function history |
| Candidate extraction/sampling | `create_v2_dataset.py`, `classify_dependency_level.py` | New manifest, stable source IDs, grouped splits and independent importability checks |
| Prompt context | `build_context_cards.py`, `prepare_v2_tier_datasets.py` | Choose one documented Pi-visible context; paper tier scores are not agent scores |
| Oracle analysis | `step4_evaluation/oracle_analysis.py` | Pin classifier, explicit SUT names, structured site evidence and new calibration |
| Runtime tracking | `instrument_oracles` and `runtime_instrumentation_pilot.py` | Reuse instrumentation inside protected execution; validate original/instrumented equivalence |
| Smells | `analyze_test_smells.py` | Expose core detectors as review suggestions; map actual detector names to rubric explicitly |
| Execution/mutation | `evaluate_results.py` and mutation helpers | Audit reconstruction/import rewriting, independent results, mounts and anti-cheating boundaries |
| Human protocol | `manual_validation/oracle_classes/PROTOCOL_V2.md` | Use for new annotation, explicitly versioned; retain original paper ratings |
| Generation | `run_realworld_experiments_v2.py` | Replace HF/GPU orchestration with Pi CLI and pinned llama.cpp endpoint |
| Review | Existing manual packages and judge tooling | New Argilla import/export; no model identity or judge anchoring in initial review |

## Issues to fix for new data

- The collector's `pushed:>` query and latest-commit date indicate repository
  activity, not function creation. Labels “leaked/unleaked” are not verified
  exposure labels. Audit relevant function/code history and use conservative
  temporal labels; no official Qwen cutoff has yet been established.
- The collector/design hard-code `2026-06-10`; this is a paper design boundary,
  not evidence of Qwen3.5's training cutoff. Select a justified new boundary.
- Collector output is hard-coded to `sources/v2_repos.json`; its dry-run path
  still reaches a write. Inspect commands before invoking them on frozen artifacts.
- The inference runner uses `/workspace` GPU paths and includes cache-deletion
  behavior. Do not execute it as the new local generation runner.
- Static assertion-presence audit is legacy evidence. Prefer `oracle_analysis`
  plus runtime reachability; specific assertions still need semantic review.
- Paper extraction repairs and its 19-task importability exclusion demonstrate
  why new reference modules need preflight validation before generation.
- Paper fail-to-pass mining produced no qualifying pairs. Do not count that
  artifact as an available bug-reproduction benchmark.
- Python 3.10 paper reproduction and Python 3.11 new deployment are separate
  environments; document differences and do not transfer scores automatically.

## Verification

Ran the existing oracle regression suite using the lab Python 3.11 environment:
`pytest tests/test_step4_evaluation/test_oracle_analysis.py -q -p no:cacheprovider`.
Result: **100 passed**. This checks classifier/instrumentation fixtures; it does
not validate the full collector, execution harness or semantic judge.

## Implemented continuation — 2026-10-10

- `scripts/evaluation/paper_pipeline_adapter.py` reads artifacts through
  `git show` at the pinned commit, refuses outputs inside the paper checkout,
  and never overwrites existing files. It exposes static oracle evidence with
  explicit unknown semantic correctness/runtime reachability and no reward credit.
- New task IDs include source identity and SHA256 rather than a modulo numeric
  ID. Smoke exports preserve original focal source without `Solution`/`self`
  rewriting and reject methods, decorators, defaults, annotations, imports and
  unresolved globals (including nested scopes) for the initial narrow L0 pilot.
- The dataset audit examined all 300 rows: 60 unresolved source revisions,
  60 unresolved license entries, one focal compile failure and one full-reference
  compile failure on the same task. No duplicate IDs were observed in this frozen
  set; the basename/modulo identity scheme remains a risk for newly collected data.
- Exported ten historical development fixtures outside Git. All ten passed
  bounded container import checks, preserving source hashes and original function
  interfaces. This is importability evidence, not verified behavioral correctness.
- Twelve new adapter regression tests passed. The existing pinned oracle suite
  remains the reference regression set; no paper source was modified.

Additional audit findings to address before fresh collection/evaluation:

- Source decoding uses `errors="ignore"`, which may discard bytes silently.
  Use Python encoding detection and fail/report decode errors in the new collector.
- Tokenizer loading/counting errors can silently bypass budget checks. New
  generation must fail clearly or record unmeasured token counts; use the exact
  deployment tokenizer/template rather than the paper's multi-model defaults.
- Filename-only identity omits repository-relative directories; numeric task
  IDs use a one-million-value modulo. Full source identity is needed for new data.
- `Solution` wrapping/self insertion changes interface; injected common imports
  and import rewriting can conceal missing reference context. Record original
  behavior and any explicit adaptation instead of silently repairing code.
- Existing import preflight executes third-party source on the host. The new
  preflight uses read-only, non-root, bounded, networkless container execution.
- Existing mutation aggregation excludes timed-out mutants from its denominator.
  Freeze a timeout/infrastructure classification policy and retain all counts;
  timeout does not by itself establish an invalid/equivalent mutant.
- Runtime oracle events are written from the generated test process, with a
  recorder accessible in that process. They are useful diagnostic evidence but
  not tamper-resistant reward evidence; adversarial verifier work is still needed.

### Contract triage of the ten smoke fixtures

Importability does not establish that the reference satisfies its documentation.
Review these distinctions before converting fixtures into scored tasks:

| Function | Contract review needed |
|---|---|
| `_parse_content_type_header` | Define supported header syntax; do not infer full standards compliance from the helper name |
| `device_focus_tokens` | Document case normalization and minimum token length |
| `_chargeback_breakdown` | Specify missing fields, UPS-versus-GPU priority, rounding and tag limits |
| `output_fn` | Supply an explicit DataFrame-like interface; L0 does not mean dependency-free inputs |
| `iter_slices` | Specify empty input and nonpositive/None slice lengths |
| `validate_subnormals` | Clarify printed output and floating-point boundary semantics before scoring |
| `_sanitize_value` | Clarify whether JSON compatibility excludes NaN/infinity; the reference passes floats through |
| `_excel_column_name` | Restrict to nonnegative integer indices or define invalid-input behavior |
| `_reverse_repeat_tuple` | Define supported repeat counts; avoid inventing negative-count requirements |
| `_agent_integrity_status` | Document missing hashes/version and canonical hash normalization |

The import probe shares one container across fixtures and captures process output.
It is a development diagnostic, not an adversarial verifier or reward boundary.
Scored execution needs per-task isolation and externally controlled evidence.

No model generation, human quality score or training has been produced by this
continuation.

## Remaining implementation

1. Independently verify smoke-task contracts and integrate bounded Pi
   test-writing/execution tools. The pinned adapter and import probe are complete;
   historical tasks remain development fixtures, not a fresh holdout.
2. Apply corrected source/date/provenance checks to collect new candidates into
   an external cache and lab manifests.
3. Validate reference modules, grouped split and task contracts, then run the
   10-task Pi pilot and import original outputs/evidence into Argilla.
4. Keep external trusted benchmark evaluation as a separate track. Reusing this
   collector does not resolve the need for independent evaluation evidence.
