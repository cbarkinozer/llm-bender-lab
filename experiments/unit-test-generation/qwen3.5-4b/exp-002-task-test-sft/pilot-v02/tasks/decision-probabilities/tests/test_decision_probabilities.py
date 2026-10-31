import json
import math
import pytest
from reflexmodels import Choice, score_decision, choice_response, fallback_gate
from reflexmodels.protocol import response_to_json


@pytest.fixture
def choice():
    return Choice('Kullanıcı dosya arıyor.', 'Hangi araç?', {'files': 'Dosyaları ara', 'web': 'Web üzerinde ara'})


def test_logits_map_to_original_option_ids(choice):
    response = score_decision(choice, request_id='r1', scorer=lambda branch: 2. if 'Dosyaları ara' in branch else 0.)
    assert response['selected_option'] == 'files'
    assert response['option_probabilities'] == pytest.approx({'files': 0.88079707798, 'web': 0.11920292202})
    gate = fallback_gate(response, min_confidence=.5)
    assert gate['margin'] == pytest.approx(.76159415596)
    p = response['option_probabilities'].values()
    assert gate['normalized_entropy'] == pytest.approx(-sum(x*math.log(x) for x in p)/math.log(2))
    assert json.loads(response_to_json(response)) == response


@pytest.mark.parametrize('probabilities', [{'files': -0.1, 'web': 1.1}, {'files': math.nan, 'web': 0.5}, {'files': 0.7, 'web': 0.7}, {'missing': 1.}])
def test_invalid_probabilities_are_rejected(choice, probabilities):
    with pytest.raises(ValueError):
        choice_response(choice, request_id='r1', probabilities=probabilities)
