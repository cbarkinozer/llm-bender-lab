from datetime import datetime, timezone
from unittest.mock import Mock


def make_app():
    from mail_workflow import MailApp
    provider = Mock()
    model = Mock()
    now = [0.0]
    app = MailApp(provider=provider, model=model, clock=lambda: now[0])
    return app, provider, model, now


def test_explicit_fetch_preserves_range_and_reports_coverage():
    app, provider, _, _ = make_app()
    app.switch_account('a')
    assert app.messages() == []
    provider.fetch.assert_not_called()
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 3, tzinfo=timezone.utc)
    row = dict(id='one', timestamp=start.timestamp(), sender='Ada', subject='Invoice', body='Approved')
    provider.fetch.return_value = [row, row]
    app.fetch(start, end)
    provider.fetch.assert_called_once_with('a', start, end)
    assert app.messages() == [row]
    assert app.search('absent', sender='Ada', start=start, end=datetime(2026, 1, 2, tzinfo=timezone.utc)) == {
        'messages': [], 'coverage': {'account': 'a', 'start': start, 'end': end},
        'scope': 'downloaded-only'}
