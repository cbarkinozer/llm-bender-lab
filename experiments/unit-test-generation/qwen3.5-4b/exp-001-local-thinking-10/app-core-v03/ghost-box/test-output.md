File: tests/test_core.py
```python
"""Mail/evidence core with explicit supplied scope and synthetic local content."""
import json
import pytest
from ghost_box.mail.store import MailStore, messages, message
from ghost_box.mail.search import search, matches
from ghost_box.mail.tasks import split_emails, TaskError
from ghost_box.mail.summary import checked_items


def mail(identifier, body='Invoice approved.', sender='İpek IŞIK', subject='Invoice'):
    return dict(id=identifier, timestamp=1, sender=sender, recipients='Team', subject=subject, body=body)


def test_session_mail_is_not_restored_and_accounts_do_not_mix():
    store = MailStore()
    store.replace('account-a', [mail('a'), mail('a')], coverage={'count': 1})
    store.replace('account-b', [mail('b')])
    assert [m['id'] for m in messages(store, 'account-a')] == ['a']
    assert [m['id'] for m in messages(store, 'account-b')] == ['b']
    assert messages(MailStore(), 'account-a') == []


def test_clear_removes_mail_and_coverage():
    store = MailStore()
    store.replace('account-a', [mail('a')], coverage={'count': 1})
    store.clear()
    assert message(store, 'account-a', 'a') is None
    assert store.coverage == {}


def test_search_respects_the_explicit_downloaded_scope():
    invoice, unrelated = mail('invoice'), mail('meeting', 'Weekly meeting.', sender='Ada', subject='Meeting')
    assert [r['id'] for r in search([invoice, unrelated], 'ipek ışık')] == ['invoice']
    assert search([unrelated], 'Invoice approved') == []
    assert search([invoice], '') == []


def test_literal_sender_filter_is_unicode_aware():
    assert matches(mail('one'), 'ipek ışık', field='sender') is True
    assert matches(mail('one'), 'Invoice', field='sender') is False


def test_long_mail_splitting_preserves_exact_unicode_content():
    body = 'Türkçe🙂 selected mail. ' * 30
    batches = split_emails([mail('one', body)], lambda items: sum(len(m['body']) + 20 for m in items), 150, 64)
    pieces = [m for batch in batches for m in batch]
    assert ''.join(m['body'] for m in pieces) == body
    assert {m['id'] for m in pieces} == {'one'}
    assert [m['part'] for m in pieces] == list(range(1, len(pieces) + 1))


def test_task_cap_does_not_silently_discard_selected_content():
    with pytest.raises(TaskError):
        split_emails([mail('one', 'x' * 1000)], lambda items: sum(len(m['body']) + 20 for m in items), 150, 2)


def test_summary_quote_cannot_be_borrowed_from_another_email():
    first = mail('one', 'The first unique original statement.') | {'key': '1:1', 'source': 1}
    second = mail('two', 'A different original fact.') | {'key': '2:1', 'source': 2}
    response = {'items': [{'key': '1:1', 'kind': 'information', 'kind_quote': first['body'], 'facts': [{'text': 'Wrong owner', 'quote': second['body']}]}, {'key': '2:1', 'kind': 'unclear', 'kind_quote': '', 'facts': []}]}
    with pytest.raises(TaskError):
        checked_items(json.dumps(response), [first, second])
```

File: tests/test_workflow.py
```python
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
```
