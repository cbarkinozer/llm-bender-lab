from unittest.mock import Mock


def make_app():
    from mail_workflow import MailApp
    provider = Mock()
    model = Mock()
    now = [0.0]
    app = MailApp(provider=provider, model=model, clock=lambda: now[0])
    return app, provider, model, now


def test_clear_removes_derived_results_and_model_idle_boundary():
    app, _, model, now = make_app()
    app.switch_account('a')
    op = app.begin_operation()
    app.finish(op, 'sensitive derived content')
    app.clear()
    assert app.result is None
    assert app.messages() == []
    app.load_model('fixture.gguf')
    app.load_model('fixture.gguf')
    model.load.assert_called_once_with('fixture.gguf')
    now[0] = 299.99
    app.check_idle()
    model.unload.assert_not_called()
    now[0] = 300.0
    app.check_idle()
    model.unload.assert_called_once_with()
    app.load_model('fixture.gguf')
    app.unload_model()
    assert model.unload.call_count == 2


def test_idle_timer_resets_and_active_operations_prevent_unload():
    app, _, model, now = make_app()
    app.load_model('fixture.gguf')
    now[0] = 299
    operation = app.begin_operation()
    now[0] = 700
    app.check_idle()
    model.unload.assert_not_called()
    assert app.finish(operation, 'done') is True
    now[0] = 999.99
    app.check_idle()
    model.unload.assert_not_called()
    now[0] = 1000
    app.check_idle()
    model.unload.assert_called_once_with()
