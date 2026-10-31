from unittest.mock import Mock
import pytest


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
