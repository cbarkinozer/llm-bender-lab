from repo_context.core import is_text_file


def test_utf8_file_is_recognized(tmp_path):
    path = tmp_path / 'notes.txt'
    path.write_text('Türkçe: ı İ ş')
    assert is_text_file(path) is True


def test_invalid_utf8_is_rejected(tmp_path):
    path = tmp_path / 'binary.bin'
    path.write_bytes(b'\xff\xfe\x00')
    assert is_text_file(path) is False
