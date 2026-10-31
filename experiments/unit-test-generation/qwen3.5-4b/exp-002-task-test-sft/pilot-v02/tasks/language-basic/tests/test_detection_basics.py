import pytest
from codelang_detect import detect


@pytest.mark.parametrize('text', ['', ' \n\t ', 'Please bring the notebook to our meeting.'])
def test_unknown_without_code_evidence(text):
    assert detect(text) == 'unknown'


@pytest.mark.parametrize('text,expected', [('def compute_total(prices):\n    return sum(prices)\n', 'py'), ('const total = prices.reduce((a, b) => a + b, 0);\nconsole.log(total);', 'js')])
def test_clear_language_markers(text, expected):
    assert detect(text) == expected
