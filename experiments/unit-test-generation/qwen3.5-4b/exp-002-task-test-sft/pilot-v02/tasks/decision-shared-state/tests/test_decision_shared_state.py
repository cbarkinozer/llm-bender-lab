import pytest
from reflexmodels import Choice, Binary, SharedStateDecisions, score_shared_state


@pytest.fixture
def choice():
    return Choice('Kullanıcı dosya arıyor.', 'Hangi araç?', {'files': 'Dosyaları ara', 'web': 'Web üzerinde ara'})


def test_shared_state_keeps_question_results_separate(choice):
    batch = SharedStateDecisions(choice.state, {'tool': choice, 'continue': Binary(choice.state, 'Devam mı?')})
    results = score_shared_state(batch, request_id='r2', scorer=lambda branch: 0., workers=1)
    assert results['tool']['option_probabilities'] == {'files': 0.5, 'web': 0.5}
    assert results['continue']['option_probabilities'] == {'yes': 0.5, 'no': 0.5}
