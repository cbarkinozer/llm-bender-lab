import io
import sys
import pytest
from codelang_detect.cli import main


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
