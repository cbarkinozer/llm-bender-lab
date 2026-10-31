File: tests/conftest.py
```python
# Snapshot tests use the public clone injection seam.
```

File: tests/test_core.py
```python
'Acceptance checks for observable application behavior.'

from repo_context.core import analyze_dependencies, build_file_tree, is_text_file, parse_github_url


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


def test_requirements_are_included_in_dependency_context(tmp_path):
    (tmp_path / 'requirements.txt').write_text('fastapi==0.115.0\npytest==8.4.2\n')
    stack, details = analyze_dependencies(tmp_path)
    assert stack == 'Python'
    assert 'requirements.txt' in details
    assert 'fastapi==0.115.0' in details and 'pytest==8.4.2' in details


def test_pyproject_dependencies_are_listed(tmp_path):
    (tmp_path / 'pyproject.toml').write_text('[project]\ndependencies = ["httpx>=0.28", "pytest>=8"]\n')
    stack, details=analyze_dependencies(tmp_path)
    assert stack == 'Python'
    assert 'pyproject.toml' in details
    assert 'httpx>=0.28' in details and 'pytest>=8' in details


def test_branch_and_subdirectory_are_separated():
    assert parse_github_url('https://github.com/owner/project/tree/main/src/pkg/') == ('https://github.com/owner/project.git', 'main', 'src/pkg')


def test_utf8_file_is_recognized(tmp_path):
    path = tmp_path / 'notes.txt'
    path.write_text('Türkçe: ı İ ş')
    assert is_text_file(path) is True


def test_invalid_utf8_is_rejected(tmp_path):
    path = tmp_path / 'binary.bin'
    path.write_bytes(b'\xff\xfe\x00')
    assert is_text_file(path) is False


```

File: tests/test_workflow.py
```python
'Acceptance checks for observable application behavior.'
from unittest.mock import Mock
import pytest


def test_shared_operation_keeps_branch_subfolder_and_safe_file_scope(tmp_path):
    from context_workflow import snapshot
    checkout = tmp_path/'repo'
    (checkout/'src').mkdir(parents=True)
    (checkout/'src'/'main.py').write_text('first\nsecond\n')
    (checkout/'src'/'.env').write_text('API_KEY=fixture-secret')
    (checkout/'src'/'ignored.py').write_text('ignored-marker')
    (checkout/'.gitignore').write_text('src/ignored.py\n')
    (checkout/'elsewhere.py').write_text('outside-subfolder')
    (checkout/'src'/'escape.py').symlink_to(checkout/'elsewhere.py')
    clone = Mock(return_value=checkout)
    text = snapshot('https://github.com/a/b/tree/dev/src', extensions=['.py'],
                    line_limit=1, token='fixture-token', clone=clone)
    clone.assert_called_once_with('https://github.com/a/b.git', branch='dev', token='fixture-token')
    assert 'first' in text and 'second' not in text
    assert 'truncat' in text.lower()
    assert all(secret not in text for secret in ['fixture-secret','fixture-token','ignored-marker','outside-subfolder'])
    assert not checkout.exists()


def test_cli_and_ui_call_the_shared_operation():
    from context_workflow import cli_snapshot, ui_snapshot
    operation = Mock(return_value='fixture markdown')
    assert cli_snapshot('https://github.com/a/b', operation=operation) == 'fixture markdown'
    assert ui_snapshot('https://github.com/a/b', operation=operation) == 'fixture markdown'
    assert operation.call_args_list[0] == operation.call_args_list[1]
    assert operation.call_count == 2


def test_invalid_url_is_not_sent_to_clone():
    from context_workflow import snapshot
    clone = Mock()
    with pytest.raises(ValueError):
        snapshot('file:///private', extensions=['.py'], line_limit=1, clone=clone)
    clone.assert_not_called()

def test_snapshot_sorts_files_and_excludes_binary_and_dependency_directories(tmp_path):
    from context_workflow import snapshot
    root=tmp_path/'checkout';root.mkdir()
    (root/'z.py').write_text('last_marker')
    (root/'a.py').write_text('first_marker')
    (root/'binary.py').write_bytes(b'\xff\xfe')
    (root/'node_modules').mkdir()
    (root/'node_modules'/'dependency.py').write_text('dependency_marker')
    text=snapshot('https://github.com/a/b',extensions=['.py'],line_limit=0,clone=Mock(return_value=root))
    assert text.index('first_marker') < text.index('last_marker')
    assert 'binary.py' not in text and 'dependency_marker' not in text
    assert not root.exists()

```
