"""One transparent diagnostic fault per task; not comprehensive mutation coverage."""
from datetime import date
import references as r

# Each fault has a concrete, contract-derived witness. Generation cannot see these.
CASES = [
    ('booking-overlap', 'has_conflict', lambda bookings, candidate: any(a <= candidate[1] and candidate[0] <= b for a,b in bookings), ([(0,10)], (10,20)), False),
    ('money-allocation', 'allocate_cents', lambda total, weights: [total*w//sum(weights) for w in weights], (2,[1,1,1]), [1,1,0]),
    ('retry-schedule', 'retry_delays', lambda *args: r.retry_delays(*args)[:-1], (5,2,2,5,11), [2,4,5]),
    ('cursor-pagination', 'page_after', lambda records,cursor,limit: [dict(x) for x in sorted(records,key=lambda x:x['id']) if cursor is None or x['id'] >= cursor][:limit], ([{'id':1},{'id':2}],1,1), [{'id':2}]),
    ('config-patch', 'merge_patch', lambda document,patch: {**document,**patch}, ({'x':1},{'x':None}), {}),
    ('business-date', 'add_business_days', lambda start,days,holidays: r.add_business_days(start,days,set()), (date(2026,12,31),1,{date(2027,1,1)}), date(2027,1,4)),
    ('interval-normalization', 'merge_intervals', lambda intervals: sorted(tuple(x) for x in intervals), ([(0,2),(2,4)],), [(0,4)]),
    ('inventory-events', 'apply_events', lambda stock,events: r.apply_events(stock,[dict(e,id=str(i)) for i,e in enumerate(events)]), ({'a':2},[{'id':'x','item':'a','delta':-1},{'id':'x','item':'a','delta':-1}]), {'a':1}),
    ('csv-import', 'parse_orders', lambda text: [], ('order_id,quantity\na,2\n',), [{'order_id':'a','quantity':2}]),
    ('price-policy', 'calculate_total', lambda items,discount_percent,shipping,free_shipping_threshold: sum(p*q for p,q in items)*(100-discount_percent)//100 + shipping, ([(101,1)],50,20,101), 50),
]


def test_fault_witnesses():
    for task, function, faulty, args, expected in CASES:
        assert getattr(r,function)(*args) == expected, task
        assert faulty(*args) != expected, task
