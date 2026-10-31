import re
import pytest
from codelang_detect import detect


def test_weighted_evidence_not_match_count(monkeypatch):
    monkeypatch.setattr('codelang_detect.detector.PATTERNS', {'first': [(re.compile('alpha'), 1), (re.compile('beta'), 1)], 'second': [(re.compile('gamma'), 3)]})
    assert detect('alpha beta gamma') == 'second'


def test_equal_scores_use_first_declared_label(monkeypatch):
    monkeypatch.setattr('codelang_detect.detector.PATTERNS', {'zeta': [(re.compile('left'), 2)], 'alpha': [(re.compile('right'), 2)]})
    assert detect('left right') == 'zeta'


def test_rule_configuration_is_read_on_every_call(monkeypatch):
    import codelang_detect.detector as detector
    monkeypatch.setattr(detector, 'PATTERNS', {'zeta':[(re.compile('runtime_marker'),1)]})
    assert detect('runtime_marker') == 'zeta'
    monkeypatch.setattr(detector, 'PATTERNS', {'alpha':[(re.compile('runtime_marker'),1)]})
    assert detect('runtime_marker') == 'alpha'


@pytest.mark.parametrize('text,expected', [('a_single_marker','one'),('no evidence','unknown')])
def test_any_positive_rule_score_qualifies(monkeypatch, text, expected):
    monkeypatch.setattr('codelang_detect.detector.PATTERNS', {'one':[(re.compile('a_single_marker'),1)]})
    assert detect(text) == expected
