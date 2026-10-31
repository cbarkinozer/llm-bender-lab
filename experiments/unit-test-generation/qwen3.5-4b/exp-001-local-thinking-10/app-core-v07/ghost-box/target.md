## Decisions and unresolved questions

Proposed decisions:

- Use one active account and keep downloaded mail and derived results in RAM.
- Local searches describe only the downloaded corpus and use Turkish-aware case folding.
- Use timezone-aware half-open date ranges for controller operations; the UI converts local selections to these bounds.

Unresolved/nonessential choices:
- Qt view layout and OAuth UX are not fixed by this contract; verify actual backend/progress integration separately.

## Proposed interface agreement

Proposed component package `ghost_box.mail` plus a public `mail_workflow.MailApp` facade. 
- `store.MailStore()` is RAM-only. `.replace(account, messages, coverage=None)` deduplicates IDs per account; `.clear()` removes all mail and coverage; `.coverage` is a mapping. `store.messages(store,account)` -> rows and `store.message(store,account,id)` -> row or None. Rows have id,timestamp,sender,recipients,subject,body. A new store is empty. Storage can retain isolated accounts; switching the active app account clears accessible state.
- `search.search(rows,query,limit=5)` returns ranked dicts with id/source/subject/score; empty query -> []. `search.matches(row,query,field="all")` -> bool, literal Turkish-aware case folding; sender filter never searches body.
- `tasks.split_emails(rows,count_tokens,context_budget,max_tasks)` -> list of batches, losslessly splitting body and preserving ID with consecutive `part` starting at 1. Raise `tasks.TaskError` rather than silently drop content when max_tasks is exceeded. `summary.checked_items(json_text, source_rows)` validates item key/kind/kind_quote/facts[{text,quote}], with source rows carrying key/source. A quotation borrowed from another source raises TaskError.
- `MailApp(provider=...,model=...,clock=...)`: provider.fetch(account,start,end) -> full rows, datetime range [start,end), aware dates. `.switch_account(id)`, `.fetch(start,end)`, `.messages()`, `.clear()`. Fetch only explicitly; deduplicate IDs. `.search(query,sender=...,start=...,end=...)` -> `{messages,coverage:{account,start,end},scope:"downloaded-only"}`, combined filters. No-results never claims global absence.
- `.answer(selected_ids,question)` passes only selected full rows to model.answer(rows,question), returns `{text,source_ids}` with selected-only citations, rejects empty/unknown IDs with ValueError. `.result` holds latest answer/operation result or None; clear/account switch removes it.
- `.begin_operation()` -> opaque handle; `.cancel(handle)`; `.finish(handle,result)` returns bool accepted. Canceled, already completed and previous-account callbacks return False and cannot replace current result.
- `.load_model(path)` calls model.load(path) once for unchanged path; `.unload_model()` releases current model through model.unload(). Clock is monotonic seconds; `.check_idle()` unloads at >=300 idle seconds, never while active operations exist; explicit model loads and successful inference reset idle activity.
Dependencies: Python, pytest; these tests do not import Qt or load weights. GUI/provider sign-in support remains separately checked.

- Literal folding maps I/İ/ı/i to i before Unicode casefold, for both queries and stored fields. Coverage always describes the downloaded range, even for narrower queries. count_tokens(list_of_row_dicts) returns an integer.
- checked_items accepts {items:[{key,kind,kind_quote,facts:[{text,quote}]}]}. kind is information/reply_requested/action_requested/unclear; unclear may have an empty kind_quote. Other kind quotes and every fact quote must occur in that item's own source body.
- .summarize(selected_ids) calls model.summarize(selected_rows), with the same selection/citation validation as answer; returns {text,source_ids}. Successful inference, load_model and begin/finish operations reset idle activity.


Public imports:
- `ghost_box.mail.search.matches`
- `ghost_box.mail.search.search`
- `ghost_box.mail.store.MailStore`
- `ghost_box.mail.store.message`
- `ghost_box.mail.store.messages`
- `ghost_box.mail.summary.checked_items`
- `ghost_box.mail.tasks.TaskError`
- `ghost_box.mail.tasks.split_emails`
- `mail_workflow.MailApp`

## Requirement-to-test map

R1: Fetch only on request for the active account and selected range.
- `tests/test_core.py::test_session_mail_is_not_restored_and_accounts_do_not_mix`
- `tests/test_workflow.py::test_explicit_fetch_preserves_range_and_reports_coverage`

R2: Search respects downloaded scope and combined filters.
- `tests/test_core.py::test_search_respects_the_explicit_downloaded_scope`
- `tests/test_core.py::test_literal_sender_filter_is_unicode_aware`
- `tests/test_workflow.py::test_explicit_fetch_preserves_range_and_reports_coverage`
- `tests/test_workflow.py::test_combined_search_filters_and_selected_inference`

R3: Selected-message inference retains provenance.
- `tests/test_core.py::test_long_mail_splitting_preserves_exact_unicode_content`
- `tests/test_core.py::test_task_cap_does_not_silently_discard_selected_content`
- `tests/test_core.py::test_summary_quote_cannot_be_borrowed_from_another_email`
- `tests/test_workflow.py::test_combined_search_filters_and_selected_inference`

R4: Cancellation does not apply stale results.
- `tests/test_workflow.py::test_cancelled_or_previous_account_result_cannot_be_applied`

R5: Account changes and clear remove old in-memory mail and derived results.
- `tests/test_core.py::test_session_mail_is_not_restored_and_accounts_do_not_mix`
- `tests/test_core.py::test_clear_removes_mail_and_coverage`
- `tests/test_workflow.py::test_cancelled_or_previous_account_result_cannot_be_applied`
- `tests/test_workflow.py::test_clear_removes_derived_results_and_model_idle_boundary`

R6: Reuse and unload local model according to explicit lifecycle.
- `tests/test_workflow.py::test_clear_removes_derived_results_and_model_idle_boundary`
- `tests/test_workflow.py::test_idle_timer_resets_and_active_operations_prevent_unload`

R7: Usable delivery, documented commands and the declared live/manual integration checks.

Manual/live: M1, M2, M3, M4

## Complete test files

File: tests/test_core.py
```python
'Acceptance checks for observable application behavior.'
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
    valid = json.loads(json.dumps(response))
    valid['items'][0]['facts'][0]['quote'] = first['body']
    assert checked_items(json.dumps(valid), [first, second])
    with pytest.raises(TaskError):
        checked_items(json.dumps(response), [first, second])
```

File: tests/test_workflow.py
```python
'Acceptance checks for observable application behavior.'
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
    assert app.search('absent', sender='Ada', start=start, end=datetime(2026, 1, 2, tzinfo=timezone.utc)) == {
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

```

## Manual checks

M1: Check native-window responsiveness, sign-in, progress, cancellation, selection and clear/account-switch controls.
M2: Check factual summaries and selected-message citations on representative messages.
M3: Observe storage to verify that mail content and derived results are not persisted.
M4: Exercise model selection, reuse and unloading with both MLX and GGUF.
