"""Private scoring references. Never include this module in generation prompts."""
from copy import deepcopy
from datetime import timedelta
import csv
import io


def integer(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError('invalid integer')


def has_conflict(bookings, candidate):
    for start, end in [*bookings, candidate]:
        if start >= end:
            raise ValueError('invalid interval')
    return any(a < candidate[1] and candidate[0] < b for a, b in bookings)


def allocate_cents(total, weights):
    integer(total)
    if not isinstance(weights, list) or not weights:
        raise ValueError('invalid weights')
    for value in weights:
        integer(value)
    denominator = sum(weights)
    if not denominator:
        raise ValueError('zero weights')
    result = [total*w // denominator for w in weights]
    order = sorted(range(len(weights)), key=lambda i: (-(total*weights[i] % denominator), i))
    for index in order[:total-sum(result)]:
        result[index] += 1
    return result


def retry_delays(attempts, initial, multiplier, cap, budget):
    for value in (attempts, initial, cap, budget):
        integer(value)
    integer(multiplier, 1)
    result, spent, delay = [], 0, min(initial, cap)
    for _ in range(attempts):
        if spent + delay > budget:
            break
        result.append(delay)
        spent += delay
        delay = min(delay * multiplier, cap)
    return result


def page_after(records, cursor, limit):
    integer(limit, 1)
    if len({r['id'] for r in records}) != len(records):
        raise ValueError('duplicate id')
    return [dict(r) for r in sorted(records, key=lambda r:r['id'])
            if cursor is None or r['id'] > cursor][:limit]


def merge_patch(document, patch):
    if not isinstance(patch, dict):
        return deepcopy(patch)
    result = deepcopy(document) if isinstance(document, dict) else {}
    for key, value in patch.items():
        if value is None:
            result.pop(key, None)
        else:
            result[key] = merge_patch(result.get(key), value)
    return result


def add_business_days(start, days, holidays):
    integer(days)
    current = start
    while days:
        current += timedelta(days=1)
        if current.weekday() < 5 and current not in holidays:
            days -= 1
    return current


def merge_intervals(intervals):
    for a, b in intervals:
        if a >= b:
            raise ValueError('invalid interval')
    result = []
    for a, b in sorted(intervals):
        if result and a <= result[-1][1]:
            result[-1] = (result[-1][0], max(b, result[-1][1]))
        else:
            result.append((a, b))
    return result


def apply_events(stock, events):
    result, seen = dict(stock), set()
    for event in events:
        if event['id'] in seen:
            continue
        seen.add(event['id'])
        quantity = result.get(event['item'], 0) + event['delta']
        if quantity < 0:
            raise ValueError('negative stock')
        result[event['item']] = quantity
    return result


def parse_orders(text):
    try:
        reader = csv.reader(io.StringIO(text, newline=''), strict=True)
        header = next(reader, None)
        if header is None or sorted(header) != ['order_id', 'quantity']:
            raise ValueError('invalid header')
        output, seen = [], set()
        for row in reader:
            if not row:
                continue
            if len(row) != 2:
                raise ValueError('invalid row')
            values = dict(zip(header, row))
            name, quantity = values['order_id'].strip(), values['quantity'].strip()
            if not name or name in seen or not quantity or any(c not in '0123456789' for c in quantity) or int(quantity) == 0:
                raise ValueError('invalid order')
            seen.add(name)
            output.append({'order_id': name, 'quantity': int(quantity)})
        return output
    except csv.Error as error:
        raise ValueError('invalid CSV') from error


def calculate_total(items, discount_percent, shipping, free_shipping_threshold):
    for value in (discount_percent, shipping, free_shipping_threshold):
        integer(value)
    if discount_percent > 100:
        raise ValueError('invalid discount')
    for price, quantity in items:
        integer(price)
        integer(quantity)
    if not items:
        return 0
    subtotal = sum(p*q for p,q in items)
    return subtotal*(100-discount_percent)//100 + (0 if subtotal >= free_shipping_threshold else shipping)
