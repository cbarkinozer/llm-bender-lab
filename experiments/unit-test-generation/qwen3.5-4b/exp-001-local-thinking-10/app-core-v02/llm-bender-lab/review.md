# llm-bender-lab — assistant review

## Whole-app request

Make me a practical Python lab for running small language-model fine-tuning experiments reproducibly. I want to define an experiment, validate conversational training data and its train/evaluation separation, save the resolved configuration, run a short training smoke through a replaceable trainer, save its adapter and metadata, evaluate the starting model and candidate under matched settings, and get a readable before/after summary. A malformed dataset or overlapping held-out examples should stop preflight rather than quietly train. Keep experiment runs in separate directories, preserve older outputs, and record model/data revisions, seed, code identity and effective settings so I can tell what actually ran. If a run fails, retain its logs and status without claiming success. Do not require a GPU, download weights or start real training when I run the lab's own tests: use a tiny fake trainer/evaluator there, but make the workflow ready to connect to a real backend. Keep credentials and large weights out of manifests and Git, distinguish unavailable metrics from zeros, and give me simple commands for preparing, running and comparing one experiment.

## Decisions and corrections

- Do not include old authored evaluation rows in training; test preprocessing with fresh fixtures.
- Keep a replaceable backend in the requested app; do not call actual GPU training from core tests.
- Preserve baseline/candidate generation settings and distinguish percentage points from relative percent.

## Important limits / missing acceptance checks

- The current application is experiment-specific scripts, not the generic orchestrator implied by the first brief.
- Current tests cover preprocessing/loss labels/padding/review but not generic run creation, backend success/failure or effective configuration comparison. Do not label this whole-app-ready.

## Requirement-to-test review

### R1 — Reject malformed conversations and held-out overlap before training.

**Core check:** Missing message roles/content or exact shared train/eval IDs/text fail validation; fake trainer has zero calls.

**Current coverage:** partial. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R2 — Resolve and preserve effective config and identities.

**Core check:** CLI override of configured learning rate appears in effective manifest while source config remains unchanged; seed/model/data/code IDs retained.

**Current coverage:** gap. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R3 — Keep runs isolated and preserve previous artifacts.

**Core check:** Two run IDs write distinct directories; attempting to reuse an existing immutable run fails without changing its original bytes.

**Current coverage:** gap. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R4 — Coordinate a smoke run and adapter artifact.

**Core check:** Fake backend receives approved inputs/settings; successful artifact and completion status agree; missing artifact cannot be labeled successful.

**Current coverage:** gap. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R5 — Keep evidence when a run fails.

**Core check:** Injected trainer error yields failed status and retained logs; no selected-success checkpoint or completed metric is fabricated.

**Current coverage:** gap. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R6 — Compare matched baseline/candidate and omit credentials.

**Core check:** Mismatched thinking/budgets raise a comparability warning/error under the agreed policy; 2/4 to 3/4 is a +25 percentage-point change; absent metrics stay unavailable; fixture secrets absent from manifest.

**Current coverage:** partial. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

## Core tests included

- `tests/test_core.py::test_preflight_accepts_expected_split_sizes`
- `tests/test_core.py::test_cross_split_duplicate_is_rejected`
- `tests/test_core.py::test_empty_answer_is_rejected`
- `tests/test_core.py::test_actual_native_labels_supervise_reasoning_and_answer`
- `tests/test_core.py::test_truncation_fails_instead_of_discarding_target`
- `tests/test_core.py::test_malformed_conversation_roles_are_rejected`
- `tests/test_core.py::test_padding_preserves_real_eos_labels`
- `tests/test_core.py::test_incomplete_reasoning_is_not_fabricated_into_an_answer`
- `tests/test_core.py::test_unrated_comparison_cannot_publish_summary`

## Manual checks

- Real adapter loading and one GPU/CPU backend smoke require separate hardware validation.
- Inspect the summary for clear scope, limits and artifact recovery instructions.
