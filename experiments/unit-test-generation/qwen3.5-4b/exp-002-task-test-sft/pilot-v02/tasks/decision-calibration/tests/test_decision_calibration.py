import math
import pytest
from reflexmodels import Choice
from reflexmodels.metrics import classification_metrics


@pytest.fixture
def choice():
    return Choice('Kullanıcı dosya arıyor.', 'Hangi araç?', {'files': 'Dosyaları ara', 'web': 'Web üzerinde ara'})


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
