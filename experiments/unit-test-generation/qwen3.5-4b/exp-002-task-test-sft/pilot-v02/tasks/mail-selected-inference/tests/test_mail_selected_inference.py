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
    narrow_end = datetime(2026, 1, 2, tzinfo=timezone.utc)
    assert app.search('invoice', sender='', start=start, end=narrow_end)['messages'] == [rows[0]]
    model.summarize.return_value = {'text':'Summary', 'source_ids':['0']}
    assert app.summarize(['0']) == {'text':'Summary', 'source_ids':['0']}
    model.summarize.assert_called_once_with([rows[0]])
    model.answer.return_value = {'text':'Foreign', 'source_ids':['1']}
    with pytest.raises(ValueError):
        app.answer(['0'], 'Status?')
    with pytest.raises(ValueError):
        app.answer(['unknown'], 'Status?')
    with pytest.raises(ValueError):
        app.answer([], 'Status?')
    assert model.answer.call_count == 2
