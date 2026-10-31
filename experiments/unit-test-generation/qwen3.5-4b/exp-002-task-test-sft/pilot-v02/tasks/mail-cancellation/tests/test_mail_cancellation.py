from unittest.mock import Mock


def make_app():
    from mail_workflow import MailApp
    provider = Mock()
    model = Mock()
    now = [0.0]
    app = MailApp(provider=provider, model=model, clock=lambda: now[0])
    return app, provider, model, now


def test_cancelled_or_previous_account_result_cannot_be_applied():
    app, _, _, _ = make_app()
    app.switch_account('a')
    old = app.begin_operation()
    app.cancel(old)
    current = app.begin_operation()
    assert app.finish(old, 'stale') is False
    assert app.finish(current, 'current') is True
    assert app.result == 'current'
    app.switch_account('b')
    assert app.result is None
    assert app.messages() == []
    assert app.finish(current, 'late from a') is False
