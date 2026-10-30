"""Trusted contract examples for preflight, not generated suites or training data."""
from datetime import date
import pytest
from references import *


def test_booking():
    assert not has_conflict([(0, 10)], (10, 20))
    assert has_conflict([(0, 10)], (9, 20))
    with pytest.raises(ValueError):
        has_conflict([(0, 10), (5, 5)], (1, 2))


def test_allocation():
    assert allocate_cents(2, [1, 1, 1]) == [1, 1, 0]
    assert allocate_cents(7, [0, 2, 1]) == [0, 5, 2]
    with pytest.raises(ValueError):
        allocate_cents(1, [True])


def test_retry():
    assert retry_delays(5, 2, 2, 5, 11) == [2, 4, 5]
    assert retry_delays(3, 0, 2, 5, 0) == [0, 0, 0]


def test_page():
    records = [{'id': 3}, {'id': 1}, {'id': 2}]
    result = page_after(records, 1, 1)
    assert result == [{'id': 2}]
    result[0]['id'] = 9
    assert records == [{'id': 3}, {'id': 1}, {'id': 2}]
    with pytest.raises(ValueError):
        page_after([{'id': 1}, {'id': 1}], None, 1)


def test_patch():
    document = {'a': {'x': 1, 'y': [2]}}
    result = merge_patch(document, {'a': {'x': None}})
    assert result == {'a': {'y': [2]}}
    result['a']['y'].append(3)
    assert document == {'a': {'x': 1, 'y': [2]}}
    assert merge_patch(5, {'a': {'b': None}}) == {'a': {}}


def test_calendar():
    assert add_business_days(date(2026, 12, 31), 1, {date(2027, 1, 1)}) == date(2027, 1, 4)
    assert add_business_days(date(2026, 10, 31), 0, set()) == date(2026, 10, 31)


def test_intervals():
    source = [[4, 5], [0, 2], [2, 4], [1, 3]]
    assert merge_intervals(source) == [(0, 5)]
    assert source == [[4, 5], [0, 2], [2, 4], [1, 3]]
    with pytest.raises(ValueError):
        merge_intervals([(1, 1)])


def test_inventory():
    source = {'a': 2}
    assert apply_events(source, [{'id': 'x', 'item': 'a', 'delta': -1}, {'id': 'x', 'item': 'a', 'delta': -99}]) == {'a': 1}
    with pytest.raises(ValueError):
        apply_events(source, [{'id': 'x', 'item': 'a', 'delta': -3}])
    assert source == {'a': 2}


def test_csv():
    assert parse_orders('quantity,order_id\n2,"a,b"\n\n3,"c\nd"\n') == [{'order_id': 'a,b', 'quantity': 2}, {'order_id': 'c\nd', 'quantity': 3}]
    for text in ['order_id,quantity\na,٢\n', 'order_id,quantity\na,1\na,2\n', 'order_id,quantity\n , \n', 'order_id,quantity\n"unclosed,2']:
        with pytest.raises(ValueError):
            parse_orders(text)


def test_price():
    assert calculate_total([(101, 1)], 50, 20, 101) == 50
    assert calculate_total([(100, 1)], 50, 20, 101) == 70
    assert calculate_total([], 0, 20, 100) == 0
    with pytest.raises(ValueError):
        calculate_total([], True, 0, 0)
