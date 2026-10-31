from repo_context.core import build_file_tree


def test_tree_filters_extensions_and_ignored_directories(tmp_path):
    (tmp_path / 'main.py').write_text('print("hello")\n')
    (tmp_path / 'image.png').write_bytes(b'\x89PNG')
    hidden = tmp_path / 'node_modules'
    hidden.mkdir()
    (hidden / 'ignored.py').write_text('not project code')
    result = build_file_tree(tmp_path, 'demo', lambda path: False, ['.py'])
    assert result.splitlines()[0] == '📂 demo'
    assert 'main.py' in result
    assert 'image.png' not in result and 'ignored.py' not in result


def test_explicit_ignore_removes_matching_file(tmp_path):
    secret = tmp_path / 'private.py'
    secret.write_text('secret = "fixture only"')
    result=build_file_tree(tmp_path, 'demo', lambda path:path == secret, ['.py'])
    assert 'private.py' not in result
    assert result.splitlines() == ['📂 demo']
