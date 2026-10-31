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

