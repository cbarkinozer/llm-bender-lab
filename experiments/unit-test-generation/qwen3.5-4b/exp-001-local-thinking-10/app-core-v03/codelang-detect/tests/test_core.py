"""Fresh examples, not the repository's retained benchmark snippet corpus."""
import io
import re
import sys
import pytest
from codelang_detect import detect
from codelang_detect.cli import main


@pytest.mark.parametrize('text', ['', ' \n\t ', 'Please bring the notebook to our meeting.'])
def test_unknown_without_code_evidence(text):
    assert detect(text) == 'unknown'


@pytest.mark.parametrize('text,expected', [('def compute_total(prices):\n    return sum(prices)\n', 'py'), ('const total = prices.reduce((a, b) => a + b, 0);\nconsole.log(total);', 'js')])
def test_clear_language_markers(text, expected):
    assert detect(text) == expected


def test_weighted_evidence_not_match_count(monkeypatch):
    monkeypatch.setattr('codelang_detect.detector.PATTERNS', {'first': [(re.compile('alpha'), 1), (re.compile('beta'), 1)], 'second': [(re.compile('gamma'), 3)]})
    assert detect('alpha beta gamma') == 'second'


def test_equal_scores_use_first_declared_language(monkeypatch):
    monkeypatch.setattr('codelang_detect.detector.PATTERNS', {'first': [(re.compile('alpha'), 2)], 'second': [(re.compile('beta'), 2)]})
    assert detect('alpha beta') == 'first'


def test_cli_file_prints_one_label(tmp_path, monkeypatch, capsys):
    path = tmp_path / 'example.py'
    path.write_text('def greet():\n    print("Merhaba dünya")\n', encoding='utf-8')
    monkeypatch.setattr(sys, 'argv', ['codelang-detect', str(path)])
    main()
    output = capsys.readouterr()
    assert (output.out, output.err) == ('py\n', '')


def test_cli_stdin_prints_one_label(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['codelang-detect'])
    monkeypatch.setattr(sys, 'stdin', io.StringIO('def square(x):\n    return x * x\n'))
    main()
    output = capsys.readouterr()
    assert (output.out, output.err) == ('py\n', '')


def test_missing_file_returns_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(sys, 'argv', ['codelang-detect', str(tmp_path / 'missing.py')])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    output = capsys.readouterr()
    assert output.out == ''
    assert "can't open" in output.err
    assert 'Traceback' not in output.err


def test_closed_stdin_returns_processing_error(monkeypatch, capsys):
    stream = io.StringIO('')
    stream.close()
    monkeypatch.setattr(sys, 'argv', ['codelang-detect'])
    monkeypatch.setattr(sys, 'stdin', stream)
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1
    output = capsys.readouterr()
    assert output.out == ''
    assert 'Error: Could not process the input.' in output.err
