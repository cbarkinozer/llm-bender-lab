from ghost_box.mail.store import MailStore, messages, message


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
