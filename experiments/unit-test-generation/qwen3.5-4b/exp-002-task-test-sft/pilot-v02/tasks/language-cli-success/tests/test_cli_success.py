import io
import sys
from codelang_detect.cli import main


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
