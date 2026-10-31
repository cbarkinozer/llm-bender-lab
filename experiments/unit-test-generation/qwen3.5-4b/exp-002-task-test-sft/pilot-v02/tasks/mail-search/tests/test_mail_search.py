from ghost_box.mail.search import search, matches


def mail(identifier, body='Invoice approved.', sender='İpek IŞIK', subject='Invoice'):
    return dict(id=identifier, timestamp=1, sender=sender, recipients='Team', subject=subject, body=body)


def test_search_respects_the_explicit_downloaded_scope():
    invoice, unrelated = mail('invoice'), mail('meeting', 'Weekly meeting.', sender='Ada', subject='Meeting')
    assert [r['id'] for r in search([invoice, unrelated], 'ipek ışık')] == ['invoice']
    assert search([unrelated], 'Invoice approved') == []
    assert search([invoice], '') == []


def test_literal_sender_filter_is_unicode_aware():
    assert matches(mail('one'), 'ipek ışık', field='sender') is True
    assert matches(mail('one'), 'Invoice', field='sender') is False
