import pytest
from ghost_box.mail.tasks import split_emails, TaskError


def mail(identifier, body='Invoice approved.', sender='İpek IŞIK', subject='Invoice'):
    return dict(id=identifier, timestamp=1, sender=sender, recipients='Team', subject=subject, body=body)


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
