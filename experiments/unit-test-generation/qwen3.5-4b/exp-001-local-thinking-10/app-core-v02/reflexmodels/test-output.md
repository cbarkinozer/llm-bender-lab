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
```
