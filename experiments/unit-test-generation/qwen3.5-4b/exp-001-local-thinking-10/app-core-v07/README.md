# Static AI review corrections — revision 07

Current demo candidates, 2026-10-31. The owner chose AI annotation for speed for
this utility demo. v06 and its original AI review remain preserved. This revision
has not received new AI ratings; it does not inherit approval for changed records.
No baseline inference or Qwen SFT has run for these whole-app prompts.

Send both files to the reviewer:

- `share/nine-examples-v07-ai-review.txt`: all nine complete inputs, rationales,
  final responses, per-requirement fault evidence and blank annotation forms,
  separated by `----`.
- `share/ai-review-response-template-v07.txt`: exact IDs, record hashes and fields.

## Changes

- Cryptocurrency returns use each series' first observed nonmissing price.
  Leading/interior gaps remain missing; nonpositive baselines fail; unavailable
  series are reported. Public calculation/provider seams replace private-helper
  dependencies; the download contract explicitly sets `auto_adjust=False`.
- Ghost-box declares folding, downloaded coverage and quotation schemas, adds
  selected-only summarization, a valid-quotation control, discriminating date
  filters, and active-operation/idle-clock checks.
- ReflexModels declares public state, ordinal identities and uncertainty output
  precisely. Fallback is tested on accepted and rejected inputs, not just failures.
- Llm-bender verifies actual train/test routing, evaluator identities, real zero
  metrics, completed status and error redaction. Shared fixtures also pass pytest
  importlib collection.
- GitHub-insignia declares authentication, query variables, sorting, mutable
  configuration and cache types. It tests credential-free saved snapshots,
  unavailable activity and profile/scope fields; security checks are separate.
- The research runner explicitly injects a local executor for trusted unit
  fixtures, retains Docker as the default for untrusted generations, and defines
  empty/skipped outcomes. Safe IDs, duplicate observations and all gates are tested.
- Repo-context checks meaningful content rather than undocumented whitespace;
  snapshots use the public clone seam and test sorting, invalid UTF-8 and
  dependency-directory exclusion.
- Miniature-llms declares losses and generation interfaces, tests odd per-head
  dimensions, and explicitly discloses that embedding/attention/feed-forward
  components are exercised through the composed model, not independently certified.
- Historical "new public/shared facade" framing is removed and flagged by the
  scanner for contextual assessment. Ordinary uses of "new" remain allowed.

## Fresh validation

- 153 passing reference cases across nine suites.
- All nine pass shuffled order seeds 17, 43 and 91.
- All 81 targeted fault probes are detected, with a detected fault for each of
  the 53 automated core requirements. This is targeted evidence, not exhaustive
  mutation coverage or proof of semantic correctness.
- All native thinking-inclusive sequences fit 8,192 tokens. Largest: 7,548;
  total across nine: 33,663. No truncation or approximate token count is used.
- Numbering, map consistency, reference/test snapshot hashes, preservation
  probes and model-text checks pass. The builder rejects stale v07 evidence.

`evidence/` contains portable execution logs, shuffled orders, actual mutation
sources, fault reports and file hashes. The runs used Python 3.13 on Windows,
separate from the previous Mac environment. `environment-windows.json` records
observed dependencies; it is not a hermetic environment lock. The authored
microfixtures use the explicitly injected local executor. These checks do not
establish the Docker isolation properties needed for untrusted model outputs.

Sources were downloaded at the recorded commits to an external artifact folder;
source checkouts were not edited. `source-snapshots.json` records Python-file
hashes and source revisions. The cryptocurrency reference is an authored local
contract implementation, not a change to the historical web app. Live UI wiring,
provider behavior and delivery checks remain visible in each example.

## Continue

Import the returned v07 AI feedback with `import_tdd_ai_review.py`; preserve
reviewer identity and method. Seven training candidates and the two held-out
repositories (GitHub-insignia and slm_test_generation) retain their roles. No
training export is created by review approval. This tiny, source-informed demo
does not establish broad generalization.

After resolving any remaining blockers, freeze prompts/splits and inference
settings, save a matched untouched-model baseline, validate native supervised
labels, then run the smoke/tiny/SFT sequence. Q4 and native BF16 comparisons
require matched deployment conditions; do not compare a Q4 baseline directly
with a native adapter run.

## Reproduce

The validation tools now accept environment overrides without changing Mac defaults:

```powershell
$env:PYTHONUTF8 = '1'
$env:TDD_ARTIFACTS = 'C:/Users/barkin/Documents/llm-bender-artifacts/tdd-v07-windows'
$env:TDD_SOURCE_ROOT = "$env:TDD_ARTIFACTS/sources"
$env:TDD_TOKENIZER_PATH = "$env:TDD_ARTIFACTS/tokenizer"
$env:TDD_PYTHON = "$env:TDD_ARTIFACTS/.venv/Scripts/python.exe"
& $env:TDD_PYTHON scripts/evaluation/run_tdd_core_suites.py --revision app-core-v07
& $env:TDD_PYTHON scripts/evaluation/check_tdd_revision_faults.py --revision app-core-v07
& $env:TDD_PYTHON scripts/evaluation/check_tdd_revision_stability.py --revision app-core-v07
& $env:TDD_PYTHON scripts/evaluation/build_tdd_app_revision.py --revision app-core-v07
```

Run from the repository root. Use the source commits in source-snapshots.json
(cbarkinozer repositories, except Prof-it/slm_test_generation), not moving heads.
The tokenizer directory contains tokenizer/config/template files only from
Qwen/Qwen3.5-4B revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a; no model
weights were downloaded for this correction. Text artifacts use UTF-8/LF so
hashes survive transfer between Windows and Mac.
