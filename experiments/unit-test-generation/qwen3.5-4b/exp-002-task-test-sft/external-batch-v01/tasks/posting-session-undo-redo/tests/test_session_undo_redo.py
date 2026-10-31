from posting.session_variables import SessionVariables


def test_revert_undo_redo_and_empty_history():
    state = SessionVariables()
    assert state.values == {}
    assert state.undo() is None
    assert state.redo() is None
    assert state.revert('missing') is False
    state.set('token', 'first')
    state.set('token', 'second')
    assert state.revert('token') is True
    assert state.values == {}
    assert state.undo() == 'token'
    assert state.values == {'token': 'second'}
    assert state.undo() == 'token'
    assert state.values == {'token': 'first'}
    assert state.redo() == 'token'
    assert state.values == {'token': 'second'}


def test_new_edit_invalidates_redo():
    state = SessionVariables()
    state.set('a', 'one')
    assert state.undo() == 'a'
    assert state.values == {}
    state.set('b', 'two')
    assert state.redo() is None
    assert state.values == {'b': 'two'}
