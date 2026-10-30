File: tests/test_core.py
```python
'Acceptance checks for observable application behavior.'
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


def test_equal_scores_use_first_declared_label(monkeypatch):
    monkeypatch.setattr('codelang_detect.detector.PATTERNS', {'zeta': [(re.compile('left'), 2)], 'alpha': [(re.compile('right'), 2)]})
    assert detect('left right') == 'zeta'


def test_cli_file_prints_one_label(tmp_path, monkeypatch, capsys):
    path = tmp_path / 'snippet.txt'
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


def test_missing_file_exits_2_with_diagnostic(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(sys, 'argv', ['codelang-detect', str(tmp_path / 'missing.py')])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    output = capsys.readouterr()
    assert output.out == ''
    assert "can't open" in output.err
    # SystemExit guards uncaught exceptions; this also rejects explicitly printed tracebacks.
    assert 'Traceback' not in output.err


def test_closed_stdin_exits_1_with_processing_error(monkeypatch, capsys):
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


def test_invalid_utf8_file_exits_1_with_processing_error(tmp_path, monkeypatch, capsys):
    path = tmp_path/'invalid.txt'
    path.write_bytes(b'\xff\xfe')
    monkeypatch.setattr(sys, 'argv', ['codelang-detect',str(path)])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1
    output = capsys.readouterr()
    assert output.out == ''
    assert output.err.startswith('Error: Could not process the input.')


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
```
