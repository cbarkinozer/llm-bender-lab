import json
import pytest
from reflexmodels import Choice, Binary, Ordinal
from reflexmodels.protocol import request_to_json


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
