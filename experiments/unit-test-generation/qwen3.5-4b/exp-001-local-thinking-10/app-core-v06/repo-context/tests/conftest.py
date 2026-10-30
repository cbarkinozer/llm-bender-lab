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
