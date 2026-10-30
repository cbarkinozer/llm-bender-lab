## Decisions and unresolved questions

Proposed decisions:

- Support simple branch names in tree URLs; do not guess slash-containing branch names.
- A positive line limit truncates; zero means unlimited. Exclude environment files and symlinks.
- CLI and UI controllers delegate to the same snapshot operation.

Unresolved/nonessential choices:
- Slash-containing branch names need a separate branch argument or an unambiguous future URL syntax.

## Proposed interface agreement

Proposed public helpers `repo_context.core` plus a new shared facade `context_workflow`:
- `parse_github_url(url)` -> (canonical .git URL,branch or None,subfolder or None); /tree/dev/src uses simple branch dev, subfolder src. Slash-containing branch names are unresolved; tests do not guess them.
- `build_file_tree(root,name,ignore,extensions)` -> deterministic tree string using 📂/📄 and box lines; ignores node_modules/generated directories and caller ignore predicate, extensions filter files. This rendering is an explicit proposed presentation convention.
- `analyze_dependencies(root)` -> (stack,Markdown details), reading requirements.txt or pyproject.toml project.dependencies; declared text layout follows supplied expected strings. `is_text_file(path)` accepts UTF-8 including Turkish, rejects invalid UTF-8.
- `core.generate_context_from_repo(url,extensions,file_line_limit=...)` -> Markdown or "Error:" string. Uses git.Repo.clone_from(url,checkout,depth=1), tempfile.mkdtemp() and returns commit hash, dependency summary, selected content, visible truncation. Clone failure includes useful reason; cleanup always. git/tempfile are explicitly declared injectable adapter seams for offline tests.
- New `context_workflow.snapshot(url,extensions=...,line_limit=...,token=None,clone=...)` -> Markdown. Accept only HTTPS github.com URLs, nonnegative line limit (0 unlimited); clone(canonical_url,branch=...,token=...) returns an owned temporary checkout path. Ownership transfers to snapshot and it deletes that checkout after success/failure. Honor root .gitignore, selected subfolder/extensions, generated dirs; exclude .env* and all symlinks. Never follow escaping symlinks. Never print token. UTF-8 files in sorted order; truncated marker when necessary. Invalid URL -> ValueError before clone.
- `cli_snapshot(url,operation=...)` and `ui_snapshot(url,operation=...)` call the same injected operation and return identical Markdown. These are controller contracts; actual CLI/Streamlit event wiring still requires a manual end-to-end check.
Dependencies: Python, pytest, GitPython, gitignore-parser, TOML reader. No real cloning in tests; docs/UI integration remains separate.

Public imports:
- `context_workflow.cli_snapshot`
- `context_workflow.snapshot`
- `context_workflow.ui_snapshot`
- `repo_context.core`
- `repo_context.core.analyze_dependencies`
- `repo_context.core.build_file_tree`
- `repo_context.core.is_text_file`
- `repo_context.core.parse_github_url`

## Requirement-to-test map

R1: Interpret repository URL and requested branch/subfolder.
- `tests/test_core.py::test_branch_and_subdirectory_are_separated`
- `tests/test_workflow.py::test_shared_operation_keeps_branch_subfolder_and_safe_file_scope`
- `tests/test_workflow.py::test_invalid_url_is_not_sent_to_clone`

R2: Respect extension and ignore policies.
- `tests/test_core.py::test_tree_filters_extensions_and_ignored_directories`
- `tests/test_core.py::test_explicit_ignore_removes_matching_file`
- `tests/test_core.py::test_utf8_file_is_recognized`
- `tests/test_core.py::test_invalid_utf8_is_rejected`
- `tests/test_workflow.py::test_shared_operation_keeps_branch_subfolder_and_safe_file_scope`

R3: Produce truthful metadata and dependencies in deterministic order.
- `tests/test_core.py::test_requirements_are_included_in_dependency_context`
- `tests/test_core.py::test_pyproject_dependencies_are_listed`
- `tests/test_core.py::test_context_workflow_reads_selected_files_and_reports_truncation`

R4: Apply and disclose line limits.
- `tests/test_core.py::test_context_workflow_reads_selected_files_and_reports_truncation`
- `tests/test_workflow.py::test_shared_operation_keeps_branch_subfolder_and_safe_file_scope`

R5: Preserve errors/cleanup and exclude credentials.
- `tests/test_core.py::test_context_workflow_reads_selected_files_and_reports_truncation`
- `tests/test_core.py::test_clone_failure_returns_error_and_cleans_temporary_directory`
- `tests/test_workflow.py::test_shared_operation_keeps_branch_subfolder_and_safe_file_scope`
- `tests/test_workflow.py::test_invalid_url_is_not_sent_to_clone`

R6: CLI and UI use the same generation operation.
- `tests/test_workflow.py::test_cli_and_ui_call_the_shared_operation`

R7: Usable delivery, documented commands and the declared live/manual integration checks.

Manual/live: M1, M2

## Complete test files

File: tests/conftest.py
```python
'Offline fixtures for application acceptance contracts.'
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import pytest



@pytest.fixture
def prepared_checkout(tmp_path, monkeypatch):
    from repo_context import core
    checkout = tmp_path / 'checkout'
    checkout.mkdir()
    (checkout / 'main.py').write_text('first_line\nsecond_line\nthird_line\n')
    (checkout / 'private.py').write_text('private_marker')
    (checkout / '.gitignore').write_text('private.py\n')
    (checkout / 'requirements.txt').write_text('pytest>=8\n')
    repository = SimpleNamespace(head=SimpleNamespace(commit=SimpleNamespace(hexsha='abc123', message='Fixture commit\n')), active_branch=SimpleNamespace(name='main'), close=Mock())
    clone = Mock(return_value=repository)
    monkeypatch.setattr(core.tempfile, 'mkdtemp', lambda: str(checkout))
    monkeypatch.setattr(core.git.Repo, 'clone_from', clone)
    return checkout, clone
```

File: tests/test_core.py
```python
'Acceptance checks for observable application behavior.'
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
```

## Manual checks

M1: Exercise actual CLI and Streamlit generate/download controls, ensuring equivalent snapshots and visible failures.
M2: Check private-repository authentication with credentials absent from the snapshot.
