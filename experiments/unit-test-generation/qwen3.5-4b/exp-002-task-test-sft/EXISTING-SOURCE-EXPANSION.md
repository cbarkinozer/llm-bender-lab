# Existing repository expansion audit - 2026-10-31

The eight task records were a deliberate two-application format pilot. They do not
exhaust the original source repositories. There is no requirement for 100 separate
repositories, nor a technical limit of ten tasks per repository.

Static inventory at the previously recorded pinned revisions:

| Repository | Role | Python modules outside tests/data exclusions | Function definitions | Test files | Test definitions |
|---|---|---:|---:|---:|---:|
| codelang-detect | training-family | 7 | 11 | 2 | 8 |
| cryptocurrency-analyser | training-family | 10 | 86 | 0 | 0 |
| ghost-box | training-family | 36 | 253 | 29 | 94 |
| GitHub-insignia | evaluation-only | 8 | 28 | 3 | 20 |
| llm-bender-lab | training-family | 215 | 678 | 86 | 514 |
| miniature-llms | training-family | 34 | 78 | 0 | 0 |
| ReflexModels | training-family | 58 | 217 | 36 | 198 |
| repo-context | training-family | 8 | 28 | 0 | 0 |
| slm_test_generation | evaluation-only | 109 | 1009 | 18 | 142 |

Counts are discovery evidence, NOT accepted dataset-row counts. They include
helpers, methods, scripts, UI and potentially redundant framework implementations.
A file may support several distinct contracts or none. Existing test definitions
are not automatically requirements-first demonstrations; task contracts, fixtures,
source exclusions and executable quality checks are still necessary. Earlier
assistant-authored lab tests are not counted as available tests in the external
source snapshots when they were absent from those pinned repositories.

## Next extraction priorities

- Ghost-box: account-isolated RAM state, downloaded search, dates, metadata,
  quotation validation, lossless task splitting, cancellation, model lifecycle,
  settings, worker state and offline provider boundaries. UI rendering needs its
  own execution environment and is not automatically an easy unit-test task.
- ReflexModels: typed requests, Unicode serialization, scoring, shared state,
  calibration, fallback, answerability and metrics. Do not turn benchmark data or
  frozen evaluation contracts into training targets.
- Llm-bender-lab: safe manifests, artifact identity, dataset/schema validation,
  orchestration and reproducibility helpers. Exclude previous evaluation examples,
  benchmark fixtures, provider secrets and one-off release operations. The large
  script count is not a license to treat every script as a useful task.
- Miniature-llms: embeddings, positions, normalization, attention, masking, cache,
  gating and numerical preservation. Group framework variants of the same behavior
  rather than presenting them as independent examples.
- Cryptocurrency-analyser: existing price math, input schemas, plotting, CSV and
  provider orchestration before introducing tasks from additional app modules.
- Repo-context: URL parsing, scoped file selection, ignores, text decoding,
  dependency summaries, limits, cleanup and CLI errors.
- Codelang-detect: remaining distinct rule, Unicode/input and CLI contracts; avoid
  inflating a small detector with many paraphrases of the same tests.

A hundred training tasks is a plausible expansion target from these families,
not an established count. Select actual distinct contracts before assigning a
per-repository quota. Preserve family-level holdout separation: GitHub-insignia
and slm_test_generation remain evaluation-only. Do not mix their files into the
training pool to reach a round number.

The next work is extraction from these existing sources. External repository
leads remain optional gap-fillers, not a prerequisite for reaching 100 rows.
