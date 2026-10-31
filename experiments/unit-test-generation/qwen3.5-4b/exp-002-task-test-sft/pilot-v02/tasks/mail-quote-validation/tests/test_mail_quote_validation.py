import json
import pytest
from ghost_box.mail.tasks import TaskError
from ghost_box.mail.summary import checked_items


def mail(identifier, body='Invoice approved.', sender='İpek IŞIK', subject='Invoice'):
    return dict(id=identifier, timestamp=1, sender=sender, recipients='Team', subject=subject, body=body)


def test_summary_quote_cannot_be_borrowed_from_another_email():
    first = mail('one', 'The first unique original statement.') | {'key': '1:1', 'source': 1}
    second = mail('two', 'A different original fact.') | {'key': '2:1', 'source': 2}
    response = {'items': [{'key': '1:1', 'kind': 'information', 'kind_quote': first['body'], 'facts': [{'text': 'Wrong owner', 'quote': second['body']}]}, {'key': '2:1', 'kind': 'unclear', 'kind_quote': '', 'facts': []}]}
    valid = json.loads(json.dumps(response))
    valid['items'][0]['facts'][0]['quote'] = first['body']
    assert checked_items(json.dumps(valid), [first, second])
    with pytest.raises(TaskError):
        checked_items(json.dumps(response), [first, second])
