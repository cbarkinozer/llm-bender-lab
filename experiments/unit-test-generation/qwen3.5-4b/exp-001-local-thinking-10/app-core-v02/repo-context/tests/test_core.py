"""Offline checks of repository context construction, not remote GitHub access."""
import sys
from pathlib import Path

from repo_context.core import analyze_dependencies, build_file_tree, is_text_file, parse_github_url


def test_tree_filters_extensions_and_ignored_directories(tmp_path):
    (tmp_path / 'main.py').write_text('print("hello")\n')
    (tmp_path / 'image.png').write_bytes(b'\x89PNG')
    hidden = tmp_path / 'node_modules'
    hidden.mkdir()
    (hidden / 'ignored.py').write_text('not project code')
    result = build_file_tree(tmp_path, 'demo', lambda path: False, ['.py'])
    assert result == '📂 demo\n└── 📄 main.py'


def test_explicit_ignore_removes_matching_file(tmp_path):
    secret = tmp_path / 'private.py'
    secret.write_text('secret = "fixture only"')
    assert build_file_tree(tmp_path, 'demo', lambda path: path == secret, ['.py']) == '📂 demo\n'


def test_requirements_are_included_in_dependency_context(tmp_path):
    (tmp_path / 'requirements.txt').write_text('fastapi==0.115.0\npytest==8.4.2\n')
    stack, details = analyze_dependencies(tmp_path)
    assert stack == 'Python'
    assert details == '**Dependencies (`requirements.txt`):**\n```\nfastapi==0.115.0\npytest==8.4.2\n\n```'


def test_pyproject_dependencies_are_listed(tmp_path):
    (tmp_path / 'pyproject.toml').write_text('[project]\ndependencies = ["httpx>=0.28", "pytest>=8"]\n')
    assert analyze_dependencies(tmp_path) == ('Python', '**Dependencies (`pyproject.toml`):**\n- httpx>=0.28\n- pytest>=8')


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


def test_context_workflow_reads_selected_files_and_reports_truncation(prepared_checkout):
    from repo_context import core
    clone_dir, clone = prepared_checkout
    result = core.generate_context_from_repo('https://github.com/owner/project', ['.py'], file_line_limit=1)
    clone.assert_called_once_with('https://github.com/owner/project.git', str(clone_dir), depth=1)
    assert '**Last Commit Hash:** abc123' in result
    assert 'first_line' in result
    assert 'second_line' not in result
    assert 'private_marker' not in result
    assert 'pytest>=8' in result
    assert 'truncat' in result.lower()
    assert clone_dir.exists() is False


def test_clone_failure_returns_error_and_cleans_temporary_directory(tmp_path, monkeypatch):
    from unittest.mock import Mock
    from repo_context import core
    checkout = tmp_path / 'checkout'
    checkout.mkdir()
    clone = Mock(side_effect=core.git.GitCommandError('clone', 128, stderr='fixture unavailable'))
    monkeypatch.setattr(core.tempfile, 'mkdtemp', lambda: str(checkout))
    monkeypatch.setattr(core.git.Repo, 'clone_from', clone)
    result = core.generate_context_from_repo('https://github.com/owner/project', ['.py'])
    assert result.startswith('Error:')
    assert 'fixture unavailable' in result
    assert checkout.exists() is False
