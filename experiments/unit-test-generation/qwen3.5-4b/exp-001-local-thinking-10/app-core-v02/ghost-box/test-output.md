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
