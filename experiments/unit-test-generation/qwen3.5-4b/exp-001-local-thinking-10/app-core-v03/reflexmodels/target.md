## Decisions and unresolved questions

These are assistant-proposed design choices for this demo, not recorded human answers.

- Use declared candidate order to resolve exact ties. Probability sums use the existing 1e-6 tolerance.
- Keep immutable runtime-defined choices and original Unicode identifiers.
- Treat empty-metric behavior as an explicit error unless a future interface specifies missing values; do not invent perfect scores.

Unresolved/nonessential choices:
- Production scoring model and acceptable calibration threshold require empirical selection.

## Proposed interface agreement

Proposed compatibility API in `reflexmodels`:
- `Choice(state,question,options)` uses ordered dict option_id -> Unicode label, at least two unique choices. `Binary(state,question)` uses yes/no; `Ordinal(state,question,labels)` rejects duplicate labels. Empty questions or invalid option structure raise ValueError. `SharedStateDecisions(state,{question_id:decision})` keeps questions/options separate.
- `score_decision(decision,request_id=...,scorer=...)`: scorer(branch_text)->logit; stable softmax maps probabilities to original option IDs and selects max, ties resolved by declaration order. Branch text includes option label. `score_shared_state(batch,request_id=...,scorer=...,workers=1)` -> question_id -> result.
- `choice_response(choice,request_id=...,probabilities={id:p})` validates exact keys, finite p in [0,1] and normalization with 1e-6 tolerance, otherwise ValueError. Returns JSON-compatible dict including selected_option and option_probabilities plus uncertainty fields. `protocol.request_to_json(request,request_id=...)` exposes state/options; `response_to_json(response)` roundtrips same dict without Unicode loss.
- `fallback_gate(response,min_confidence=...,min_margin=0,answerability_probability=None,min_answerability=...)` -> dict with fallback_required bool, reason_codes list. Low margin -> low_margin; insufficient answerability -> insufficient_evidence, independently of confident option.
- `metrics.classification_metrics(labels,probabilities,ece_bins=15)` -> accuracy,macro_f1,nll,brier,ece floats. labels zero-based; probability rows same normalized class count>=2. Empty input/invalid bins raise ValueError. Macro-F1 includes all probability columns (undefined per-class F1 contributes 0). NLL uses true-class probabilities; Brier sums squared multiclass errors then averages; ECE is weighted top-label confidence/accuracy discrepancy. Exact ties use first index. For [.75,.25] and [.25,.75] with correct labels, NLL=-log(.75), Brier=.125, ECE=.25.
Dependencies: Python standard library, pytest. Local model quality/calibration on real traffic remains an empirical/manual check.

Declared application import inventory (checked against test AST):
- `reflexmodels.Binary`
- `reflexmodels.Choice`
- `reflexmodels.Ordinal`
- `reflexmodels.SharedStateDecisions`
- `reflexmodels.choice_response`
- `reflexmodels.fallback_gate`
- `reflexmodels.score_decision`
- `reflexmodels.score_shared_state`
- `reflexmodels.metrics.classification_metrics`
- `reflexmodels.protocol.request_to_json`
- `reflexmodels.protocol.response_to_json`

## Requirement-to-test map

R1: Accept runtime-defined Unicode option identifiers and validate request types.
- `tests/test_core.py::test_runtime_unicode_options_roundtrip`
- `tests/test_core.py::test_invalid_decision_requests_are_rejected`

R2: Produce correct option probabilities and selected IDs.
- `tests/test_core.py::test_logits_map_to_original_option_ids`

R3: Validate probability domain and normalization.
- `tests/test_core.py::test_invalid_probabilities_are_rejected`

R4: Keep shared-state questions isolated.
- `tests/test_core.py::test_shared_state_keeps_question_results_separate`

R5: Route ambiguous or unanswerable outcomes to fallback.
- `tests/test_core.py::test_low_margin_requires_fallback`
- `tests/test_core.py::test_low_answerability_overrides_confident_choice`

R6: Report reproducible metrics and undefined cases.
- `tests/test_core.py::test_metrics_include_unpredicted_class`
- `tests/test_core.py::test_calibration_metrics_have_concrete_expected_values`
- `tests/test_core.py::test_undefined_metrics_reject_invalid_inputs`

R7: Usable delivery, documented commands and the declared live/manual integration checks.

Manual/live: M1, M2

## Complete test files

File: tests/test_core.py
```python
"""Observable request, scoring, routing and metric contracts; no model needed."""
import json
import math
import pytest
from reflexmodels import Choice, Binary, Ordinal, SharedStateDecisions, score_decision, score_shared_state, choice_response, fallback_gate
from reflexmodels.protocol import request_to_json, response_to_json
from reflexmodels.metrics import classification_metrics


@pytest.fixture
def choice():
    return Choice('Kullanıcı dosya arıyor.', 'Hangi araç?', {'files': 'Dosyaları ara', 'web': 'Web üzerinde ara'})


def test_runtime_unicode_options_roundtrip(choice):
    encoded = json.loads(request_to_json(choice, request_id='r1'))
    assert encoded['options'] == {'files': 'Dosyaları ara', 'web': 'Web üzerinde ara'}
    assert encoded['state'] == 'Kullanıcı dosya arıyor.'


@pytest.mark.parametrize('factory', [lambda: Choice('state', 'question', {'one': 'Only'}), lambda: Ordinal('state', 'question', ('low', 'low')), lambda: Binary('state', '')])
def test_invalid_decision_requests_are_rejected(factory):
    with pytest.raises(ValueError):
        factory()


def test_logits_map_to_original_option_ids(choice):
    response = score_decision(choice, request_id='r1', scorer=lambda branch: 2. if 'Dosyaları ara' in branch else 0.)
    assert response['selected_option'] == 'files'
    assert response['option_probabilities'] == pytest.approx({'files': 0.88079707798, 'web': 0.11920292202})
    assert json.loads(response_to_json(response)) == response


@pytest.mark.parametrize('probabilities', [{'files': -0.1, 'web': 1.1}, {'files': math.nan, 'web': 0.5}, {'files': 0.7, 'web': 0.7}, {'missing': 1.}])
def test_invalid_probabilities_are_rejected(choice, probabilities):
    with pytest.raises(ValueError):
        choice_response(choice, request_id='r1', probabilities=probabilities)


def test_shared_state_keeps_question_results_separate(choice):
    batch = SharedStateDecisions(choice.state, {'tool': choice, 'continue': Binary(choice.state, 'Devam mı?')})
    results = score_shared_state(batch, request_id='r2', scorer=lambda branch: 0., workers=1)
    assert results['tool']['option_probabilities'] == {'files': 0.5, 'web': 0.5}
    assert results['continue']['option_probabilities'] == {'yes': 0.5, 'no': 0.5}


def test_low_margin_requires_fallback(choice):
    response = choice_response(choice, request_id='r', probabilities={'files': 0.51, 'web': 0.49})
    gate = fallback_gate(response, min_confidence=.5, min_margin=.2)
    assert gate['fallback_required'] is True
    assert 'low_margin' in gate['reason_codes']


def test_low_answerability_overrides_confident_choice(choice):
    response = choice_response(choice, request_id='r', probabilities={'files': .9, 'web': .1})
    gate = fallback_gate(response, min_confidence=.8, answerability_probability=.2, min_answerability=.7)
    assert gate['fallback_required'] is True
    assert 'insufficient_evidence' in gate['reason_codes']


def test_metrics_include_unpredicted_class():
    result = classification_metrics([0, 1], [[.9, .1], [.8, .2]])
    assert result['accuracy'] == .5
    assert result['macro_f1'] == pytest.approx(1 / 3)


def test_calibration_metrics_have_concrete_expected_values():
    result = classification_metrics([0,1], [[.75,.25],[.25,.75]], ece_bins=2)
    assert result == pytest.approx({'accuracy':1., 'macro_f1':1.,
        'nll':-math.log(.75), 'brier':.125, 'ece':.25})


@pytest.mark.parametrize('labels,probabilities,bins', [([],[],2),([0],[[1.,0.]],0)])
def test_undefined_metrics_reject_invalid_inputs(labels, probabilities, bins):
    with pytest.raises(ValueError):
        classification_metrics(labels, probabilities, ece_bins=bins)
```

## Manual checks

M1: Actual local-model latency, memory use, semantic decisions and calibration on fresh data require separate evaluation.
M2: Run the documented local request-to-response example; inspect uncertainty fields against the documented schema.
