from posting.session_variables import SessionVariables


def test_fifty_edit_retention_boundary():
    state = SessionVariables()
    for index in range(55):
        state.set('key', str(index))
    for _ in range(50):
        assert state.undo() == 'key'
    assert state.values == {'key': '4'}
    assert state.undo() is None


def test_script_value_restored_without_type_coercion():
    state = SessionVariables()
    state.values['number'] = 42
    assert state.undo() is None
    state.set('number', 'editor text')
    assert state.undo() == 'number'
    assert state.values['number'] == 42
    assert type(state.values['number']) is int
