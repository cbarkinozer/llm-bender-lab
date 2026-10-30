"""Proposed app workflow contracts: fake providers, clock and model only."""
from datetime import datetime, timezone
from unittest.mock import Mock
import pytest


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
    assert app.search('absent', sender='Ada', start=start, end=end) == {
        'messages': [], 'coverage': {'account': 'a', 'start': start, 'end': end},
        'scope': 'downloaded-only'}


def test_combined_search_filters_and_selected_inference():
    app, provider, model, _ = make_app()
    app.switch_account('a')
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 3, tzinfo=timezone.utc)
    rows = [dict(id=str(i), timestamp=start.timestamp()+i*86400, sender=sender,
                 subject='Invoice', body='Approved') for i, sender in enumerate(['Ada', 'Bob'])]
    provider.fetch.return_value = rows
    app.fetch(start, end)
    assert app.search('invoice', sender='Ada', start=start, end=end)['messages'] == [rows[0]]
    model.answer.return_value = {'text': 'Approved', 'source_ids': ['0']}
    assert app.answer(['0'], 'Status?') == {'text': 'Approved', 'source_ids': ['0']}
    model.answer.assert_called_once_with([rows[0]], 'Status?')
    with pytest.raises(ValueError):
        app.answer([], 'Status?')
    model.answer.assert_called_once()


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
