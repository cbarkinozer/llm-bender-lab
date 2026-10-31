## Decisions and unresolved questions

Proposed decisions:

- Use Python (py) and JavaScript (js) as the initial supported language targets; additional languages remain open under M2.
- Treat any positive configured rule score as sufficient evidence. No additional confidence threshold is applied.
- Equal weighted scores choose the first declared output label, not alphabetical order. Read the public PATTERNS mapping on every call.
- Read file contents rather than the filename suffix. File-open usage failures exit 2; read/processing failures, including invalid UTF-8, exit 1 without a traceback.

Unresolved/nonessential choices:
- Additional supported languages beyond Python/JavaScript and accuracy expectations for ambiguous snippets remain open under M2.

## Proposed interface agreement

Proposed public API:
- `codelang_detect.detect(text)` returns the lowercase output label of the highest-scoring rule group, or "unknown" for empty/whitespace input or no positive evidence. The initial supported language targets are Python (`py`) and JavaScript (`js`); additional languages remain open under M2. This does not prohibit additional configured labels.
- `codelang_detect.detector.PATTERNS` is the public developer-configuration mapping, read from that module on every `detect` call. Replacing it takes effect immediately; the function does not retain an import-time or first-call copy. It is insertion-ordered: output_label -> list[(compiled regex, positive weight)]. Keys are the labels returned by `detect`, including custom labels in controlled rule configurations.
- Each matching regex contributes its weight once. Any strictly positive total score qualifies; there is no higher minimum-score threshold. The greatest total wins. Equal positive totals choose the first declared key, even when alphabetical order differs. All-zero scores return "unknown". This rule-based score is not a statistical confidence estimate.
- `codelang_detect.cli.main()` reads sys.argv, an optional UTF-8 file or sys.stdin. Detect from contents, irrespective of filename suffix. Print exactly one label plus newline to stdout.
- File-open/usage failure raises SystemExit(2), with useful stderr mentioning "can't open" and no stdout. Read/processing failure, including invalid UTF-8 bytes or closed stdin, raises SystemExit(1), with stderr starting "Error: Could not process the input." and no stdout. Do not print tracebacks or propagate unexpected exceptions in normal input-error cases.
Dependencies: standard library only at application runtime; pytest for tests. Packaging, examples and additional language accuracy are separate manual checks.

Public imports and configuration:
- `codelang_detect.detect`
- `codelang_detect.cli.main`
- `codelang_detect.detector` (module)
- `codelang_detect.detector.PATTERNS`

## Requirement-to-test map

R1: Return unknown for input without supported evidence.
- `tests/test_core.py::test_unknown_without_code_evidence`
- `tests/test_core.py::test_any_positive_rule_score_qualifies`

R2: Use weighted evidence and deterministic ties.
- `tests/test_core.py::test_weighted_evidence_not_match_count`
- `tests/test_core.py::test_equal_scores_use_first_declared_label`
- `tests/test_core.py::test_rule_configuration_is_read_on_every_call`
- `tests/test_core.py::test_any_positive_rule_score_qualifies`

R3: Recognize approved unambiguous starter-language examples.
- `tests/test_core.py::test_clear_language_markers`

R4: File and stdin CLI routes match the library.
- `tests/test_core.py::test_cli_file_prints_one_label`
- `tests/test_core.py::test_cli_stdin_prints_one_label`

R5: Input failures use nonzero exit and useful diagnostics.
- `tests/test_core.py::test_missing_file_exits_2_with_diagnostic`
- `tests/test_core.py::test_closed_stdin_exits_1_with_processing_error`
- `tests/test_core.py::test_invalid_utf8_file_exits_1_with_processing_error`

R6: Usable delivery, documented commands and the declared live/manual integration checks.

Manual/live: M1, M2

## Complete test files

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

## Manual checks

M1: Run installation instructions and documented examples.
M2: Choose additional language targets beyond Python and JavaScript, document their labels, and add acceptance cases before declaring them supported. Evaluate ambiguous snippets separately.
