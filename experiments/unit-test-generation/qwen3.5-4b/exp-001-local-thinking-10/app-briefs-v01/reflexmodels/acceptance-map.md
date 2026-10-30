# ReflexModels — draft core acceptance map

Complete decision toolkit MVP; training a new decision model and mobile deployment are separate workflows.

These are proposed checks, not an executed suite or proof of complete coverage.

| ID | Observable requirement | Concrete oracle / core check | Level |
|---|---|---|---|
| R1 | Accept runtime-defined Unicode option identifiers and validate request types. | Round-trip Turkish option text/IDs; one-option choice and duplicate ordinal levels fail with explicit errors. | unit |
| R2 | Produce correct option probabilities and selected IDs. | Injected logits [0,0] produce 0.5/0.5; logit difference 2 produces approximately 0.880797/0.119203; selected ID maps to the original option, not position text. | unit |
| R3 | Validate probability domain and normalization. | Negative, nonfinite or inconsistent probability inputs are rejected under an explicit tolerance; valid zero/one probabilities retain meaning. | unit |
| R4 | Keep shared-state questions isolated. | Two questions with overlapping display text but different IDs return their own result keys/options; no cross-question score leakage. | integration |
| R5 | Route ambiguous or unanswerable outcomes to fallback. | 0.51/0.49 below the chosen margin triggers low-margin fallback; 0.9 confidence with 0.2 answerability triggers insufficient-evidence fallback. | unit |
| R6 | Report reproducible metrics and undefined cases. | A fixed four-item prediction fixture yields exact accuracy/confusion counts; empty/undefined metrics use the agreed unavailable representation instead of a perfect score. | unit |

## Public test boundary (proposal)

Typed request/response, injectable score callable, batch operation and fallback/evaluation API. No fixed tool taxonomy imposed.

## Decisions still needing agreement

- Agree tie-breaking, probability-sum tolerance and empty-metric representation.
- Confirm whether calibration fitting is part of the core app or only evaluation of supplied calibrated probabilities.

## Manual / live checks

- Actual local-model latency, memory use, semantic decisions and calibration on fresh data require separate evaluation.

## Candidate existing evidence — not automatically selected

- `tests/test_types.py`
- `tests/test_serialization.py`
- `tests/test_scoring.py`
- `tests/test_routing.py`
- `tests/test_metrics.py`
- `tests/test_calibration.py`

Source revision: `efbc154cf9b9caf41a6e68a314356eed96dbb017`. These prompts are reconstructed drafts, not historical original user messages. Split role is unassigned; never use the same app/scenario for both SFT and claimed held-out improvement.
