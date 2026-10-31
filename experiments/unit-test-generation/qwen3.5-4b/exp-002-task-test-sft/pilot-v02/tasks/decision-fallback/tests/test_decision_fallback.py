import pytest
from reflexmodels import Choice, choice_response, fallback_gate


@pytest.fixture
def choice():
    return Choice('Kullanıcı dosya arıyor.', 'Hangi araç?', {'files': 'Dosyaları ara', 'web': 'Web üzerinde ara'})


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


def test_fallback_accepts_confident_answerable_choice_and_rejects_low_confidence(choice):
    response = choice_response(choice, request_id='r', probabilities={'files':.9,'web':.1})
    gate = fallback_gate(response, min_confidence=.8, min_margin=.2,
                         answerability_probability=.9, min_answerability=.7)
    assert gate['fallback_required'] is False
    assert gate['reason_codes'] == []
    assert gate['accepted'] is True
    uncertain = choice_response(choice, request_id='u', probabilities={'files':.6,'web':.4})
    rejected = fallback_gate(uncertain, min_confidence=.8)
    assert rejected['fallback_required'] is True
    assert rejected['reason_codes'] == ['low_confidence']
