import pytest
from reflexmodels import Choice, Ordinal, score_decision


@pytest.fixture
def choice():
    return Choice('Kullanıcı dosya arıyor.', 'Hangi araç?', {'files': 'Dosyaları ara', 'web': 'Web üzerinde ara'})


def test_ordinal_scoring_and_declaration_order_ties(choice):
    ordinal = Ordinal('state', 'Priority?', ('low','medium','high'))
    result = score_decision(ordinal, request_id='o', scorer=lambda branch:2. if 'medium' in branch else 0.)
    assert result['selected_option'] == 'medium'
    assert list(result['option_probabilities']) == ['low','medium','high']
    tie = Choice('state', 'Pick?', {'zeta':'Z', 'alpha':'A'})
    assert score_decision(tie, request_id='t', scorer=lambda branch:0.)['selected_option'] == 'zeta'
