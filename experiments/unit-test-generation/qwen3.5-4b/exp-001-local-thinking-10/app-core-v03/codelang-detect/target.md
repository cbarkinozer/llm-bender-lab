## Decisions and unresolved questions

These are assistant-proposed design choices for this demo, not recorded human answers.

- Choose Python and JavaScript as explicit starter examples; extending language coverage is a later agreed requirement.
- Equal weighted scores choose the first declared language; rules are developer configuration, not a new runtime configuration service.
- File-open CLI usage failures exit 2; processing failures exit 1. Both are nonzero and use stderr. The first draft wrongly assumed all errors exit 1.

Unresolved/nonessential choices:
- Accuracy expectations for ambiguous mixed-language snippets remain open.

## Proposed interface agreement

Proposed `codelang_detect.detect(text)` -> lowercase extension string, or "unknown" for empty/prose/no matching rule. Starter contract explicitly includes Python def/return and JavaScript const/reduce/console.log examples; other language coverage is not certified by these examples.
- Developer configuration `codelang_detect.detector.PATTERNS`: insertion-ordered language -> list[(compiled regex,positive weight)]. Score is sum of weights for matching rules, not first match or number of matched rules. Equal positive scores select first declared language; all-zero -> unknown. It is a documented configuration seam, not an accidental private patch.
- `codelang_detect.cli.main()` reads sys.argv, file positional argument or sys.stdin; writes exactly label + newline to stdout. UTF-8 file open error -> SystemExit(2), useful stderr mentioning "can't open", no traceback. Processing/closed-stdin error -> SystemExit(1), stderr "Error: Could not process the input.", no stdout.
Dependencies: standard library only at application runtime; pytest for tests. Packaging/examples and additional language accuracy are separately checked.

Declared application import inventory (checked against test AST):
- `codelang_detect.detect`
- `codelang_detect.cli.main`

## Requirement-to-test map

R1: Return unknown for input without supported evidence.
- `tests/test_core.py::test_unknown_without_code_evidence`

R2: Use weighted evidence and deterministic ties.
- `tests/test_core.py::test_weighted_evidence_not_match_count`
- `tests/test_core.py::test_equal_scores_use_first_declared_language`

R3: Recognize approved unambiguous starter-language examples.
- `tests/test_core.py::test_clear_language_markers`

R4: File and stdin CLI routes match the library.
- `tests/test_core.py::test_cli_file_prints_one_label`
- `tests/test_core.py::test_cli_stdin_prints_one_label`

R5: Input failures use nonzero exit and useful diagnostics.
- `tests/test_core.py::test_missing_file_returns_error`
- `tests/test_core.py::test_closed_stdin_returns_processing_error`

R6: Usable delivery, documented commands and the declared live/manual integration checks.

Manual/live: M1, M2

## Complete test files

File: tests/test_core.py
```python
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
```

## Manual checks

M1: Responsiveness on representative file sizes and real-world accuracy require separate benchmarks.
M2: Run installation and documented examples; additional supported languages require their own held-out accuracy evaluation.
