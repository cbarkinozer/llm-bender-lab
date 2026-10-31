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


