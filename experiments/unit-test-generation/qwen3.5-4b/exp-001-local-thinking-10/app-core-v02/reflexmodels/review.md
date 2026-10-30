# ReflexModels — assistant review

## Whole-app request

Build me a small Python decision-model toolkit for applications that need quick structured decisions rather than generated paragraphs. A caller should provide shared state, a natural-language question and options defined at runtime, including Turkish labels; support binary, choice and ordered-level decisions. Return stable typed results with the original option identifiers, probabilities, selected answer and uncertainty information, and let several questions share one state without mixing their options. Keep the scorer replaceable so I can use deterministic scores in tests and later connect a local model. Validate malformed requests, duplicate options and invalid probabilities rather than silently repairing them. Provide a configurable fallback decision when confidence, margin or answerability is insufficient, and evaluation/calibration helpers that report honest metrics, including undefined cases. Preserve Unicode and stable serialization so another process can consume results, don't train or download anything merely to test the toolkit, and document a complete local example from request through scoring to response and fallback.

## Decisions and corrections

- Use declared candidate order to resolve exact ties. Probability sums use the existing 1e-6 tolerance.
- Keep immutable runtime-defined choices and original Unicode identifiers.
- Treat empty-metric behavior as an explicit error unless a future interface specifies missing values; do not invent perfect scores.

## Important limits / missing acceptance checks

- Core tests cover types/scoring/routing/metrics; calibration fitting, empty metrics and all serialization validation branches need further checks.
- Semantic decision quality and CPU latency are separate from injected-score arithmetic.

## Requirement-to-test review

### R1 — Accept runtime-defined Unicode option identifiers and validate request types.

**Core check:** Round-trip Turkish option text/IDs; one-option choice and duplicate ordinal levels fail with explicit errors.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R2 — Produce correct option probabilities and selected IDs.

**Core check:** Injected logits [0,0] produce 0.5/0.5; logit difference 2 produces approximately 0.880797/0.119203; selected ID maps to the original option, not position text.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R3 — Validate probability domain and normalization.

**Core check:** Negative, nonfinite or inconsistent probability inputs are rejected under an explicit tolerance; valid zero/one probabilities retain meaning.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R4 — Keep shared-state questions isolated.

**Core check:** Two questions with overlapping display text but different IDs return their own result keys/options; no cross-question score leakage.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R5 — Route ambiguous or unanswerable outcomes to fallback.

**Core check:** 0.51/0.49 below the chosen margin triggers low-margin fallback; 0.9 confidence with 0.2 answerability triggers insufficient-evidence fallback.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R6 — Report reproducible metrics and undefined cases.

**Core check:** A fixed four-item prediction fixture yields exact accuracy/confusion counts; empty/undefined metrics use the agreed unavailable representation instead of a perfect score.

**Current coverage:** partial. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

## Core tests included

- `tests/test_core.py::test_runtime_unicode_options_roundtrip`
- `tests/test_core.py::test_invalid_decision_requests_are_rejected`
- `tests/test_core.py::test_logits_map_to_original_option_ids`
- `tests/test_core.py::test_invalid_probabilities_are_rejected`
- `tests/test_core.py::test_shared_state_keeps_question_results_separate`
- `tests/test_core.py::test_low_margin_requires_fallback`
- `tests/test_core.py::test_low_answerability_overrides_confident_choice`
- `tests/test_core.py::test_metrics_include_unpredicted_class`

## Manual checks

- Actual local-model latency, memory use, semantic decisions and calibration on fresh data require separate evaluation.
