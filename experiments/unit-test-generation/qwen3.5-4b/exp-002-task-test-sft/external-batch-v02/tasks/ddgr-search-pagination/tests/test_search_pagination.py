import pytest
from ddgr import DdgUrl


def test_pagination_transitions_and_reset():
    url = DdgUrl(duration='', keywords=['python'])
    assert (url.query()['page'], url.query()['curindex']) == (0, 1)
    url.update_num(10)
    url.next_page()
    assert (url.query()['page'], url.query()['curindex']) == (1, 11)
    url.next_page()
    assert (url.query()['page'], url.query()['curindex']) == (2, 21)
    url.prev_page()
    assert (url.query()['page'], url.query()['curindex']) == (1, -21)
    url.first_page()
    assert (url.query()['page'], url.query()['curindex']) == (0, 1)
    assert url.query()['q'] == 'python'


def test_first_page_boundaries():
    url = DdgUrl(duration='')
    with pytest.raises(ValueError):
        url.prev_page()
    with pytest.raises(ValueError):
        url.first_page()
    assert url.query()['page'] == 0
