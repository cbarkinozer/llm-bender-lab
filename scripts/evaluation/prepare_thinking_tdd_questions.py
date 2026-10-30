"""Version the ten requirement-only questions and publish a clean approval view."""
import hashlib
import json
from pathlib import Path
import uuid
import argilla as rg

ROOT=Path(__file__).resolve().parents[2]
DOMAIN=ROOT/'experiments/unit-test-generation/qwen3.5-4b'
EXP=DOMAIN/'exp-001-local-thinking-10'
DEST=EXP/'questions-v02'
SYSTEM='''You write Python unit tests from requirements before the implementation exists. Use pytest and the Python standard library only. The public API below is an agreed interface, not implementation code. Do not implement the function or assume undocumented behavior. First reason about concrete expected outcomes, boundaries, validation and input preservation in the model's native thinking channel. In the final answer return one Python code block containing a complete executable pytest module, importing the function from solution. Use deterministic isolated tests, clear scenario names and specific contract-derived assertions. Avoid redundant cases, unnecessary branching and unrelated checks. Exact assertions must be correct; assertion strength alone does not establish correctness.'''

CONTRACTS=[
('Booking conflict detection',[
'bookings is a list of intervals; each interval is a two-element tuple or list (start, end). candidate is one such interval. Endpoints are integer minute offsets. Example input shapes: bookings=[(10, 20), (30, 40)], candidate=(20, 30).',
'Intervals are half-open: the start is included and the end is excluded. Return a bool indicating whether candidate overlaps at least one booking. Touching endpoints alone do not conflict. Empty bookings returns False for a valid candidate.',
'Every booking and candidate must have start < end. Otherwise raise ValueError. Validate all intervals, even if an earlier booking already overlaps candidate.',
'Preserve both inputs. Other malformed input shapes and non-integer endpoints are outside this contract.']),
('Proportional allocation of integer cents',[
'Total is a nonnegative built-in int. weights is a nonempty list of nonnegative built-in ints with a positive sum. Booleans are invalid. Invalid types or domain values raise ValueError.',
'For each index i, calculate total * weights[i] / sum(weights). Start with the floor of each share. Distribute the remaining cents one per index in descending fractional-remainder order; ties go to the lower original index.',
'Return a list of built-in ints in original index order whose sum equals total. Zero total and individual zero weights are valid. Preserve weights.']),
('Retry delays under a cumulative budget',[
'All arguments must be built-in ints, excluding bool. attempts, initial, cap and budget are nonnegative; multiplier is at least 1. Invalid arguments raise ValueError.',
'Return a list of at most attempts delays. The delay at zero-based position i is min(initial * multiplier**i, cap).',
'Append a delay if adding it keeps the cumulative sum less than or equal to budget. Stop at the first unaffordable delay. A delay that exactly exhausts the budget is included.',
'Zero delays are permitted and consume an attempt. Zero attempts returns an empty list after argument validation.']),
('Pagination after an exclusive cursor',[
'records is a list of dictionaries, each with an integer id key. cursor is an integer or None. All other record fields are arbitrary values. These types are guaranteed except for limit.',
'limit must be a positive built-in int, excluding bool; otherwise raise ValueError. Duplicate record ids raise ValueError even if those records would be outside the requested page.',
'Sort records by ascending id. If cursor is not None, keep only records with id strictly greater than cursor. Return at most limit records as a list; empty results are valid.',
'Each returned dictionary is a fresh shallow copy. Do not change input ordering or contents. Nested values may be shared because the copy is shallow.']),
('Recursive JSON merge patch',[
'document and patch are Python JSON-compatible values: dictionaries with string keys, lists, strings, numbers, bool or None. No malformed-input behavior is required.',
'If patch is not a dictionary, return a deep copy of patch, replacing document completely.',
'If patch is a dictionary, start from document when it is a dictionary, or an empty dictionary otherwise. For each patch key: None deletes the key if present; a dictionary value recursively applies these same rules; every other value replaces the existing value with a deep copy.',
'Return the merged value. Neither input may change. No nested mutable list or dictionary in the result may alias either input, including unchanged document branches.']),
('Business-day date arithmetic',[
'start is a datetime.date and holidays is a set of datetime.date values. days must be a nonnegative built-in int, excluding bool; invalid days raises ValueError. Other input types are guaranteed.',
'Return the date reached by counting days business days strictly after start. A business day is Monday through Friday and not in holidays.',
'For days=0, return start even if it falls on a weekend or holiday. Handle month and year transitions. The resulting date is guaranteed representable.',
'Preserve holidays. Tests must use fixed dates rather than the current clock.']),
('Normalize overlapping or touching intervals',[
'intervals is a list of two-element tuples or lists (start, end), with integer endpoints. Input order may be arbitrary. Other malformed shapes and endpoint types are outside scope.',
'Every interval must have start < end. Validate all intervals and raise ValueError if any interval is invalid.',
'Return a new list of tuples sorted by start, merging all overlapping or touching intervals into their union. Handle containment, duplicates and chains of overlaps. Empty input returns an empty list.',
'Preserve the original list ordering and nested interval contents. Return tuples rather than reusing mutable input intervals.']),
('Apply inventory events with idempotency',[
'stock is a dictionary mapping item-name strings to nonnegative integer quantities. events is an ordered list of dictionaries, each containing string id, string item and integer delta. Input types and initial stock quantities are guaranteed valid.',
'Process events in order. Apply only the first occurrence of each event id. Ignore every later occurrence completely, even if its item or delta differs.',
'For a first-occurrence event, missing items start at zero. Add delta; if the resulting quantity would be negative, raise ValueError immediately. Keep items whose final quantity is zero.',
'Return a fresh stock dictionary. Neither stock nor events may change, including when an exception occurs.']),
('Import orders from CSV text',[
'Input text is a string containing CSV with comma delimiters and standard double-quote escaping, as parsed by Python csv.reader with strict=True. Quoted commas and quoted newlines are supported. Parser-detected quoting errors raise ValueError.',
'The first record must contain exactly the header names order_id and quantity, in either order, with no duplicates or extra fields. Header names are exact and are not stripped. Missing or invalid headers raise ValueError.',
'Ignore only empty CSV records with zero fields. Every other data record must contain exactly two fields; whitespace-only fields are not ignored.',
'Strip leading and trailing whitespace from each data field. order_id must be nonempty and unique after stripping. quantity must contain only ASCII digits and represent a positive integer. Leading zeroes are permitted. Invalid records raise ValueError.',
'Return a list of dictionaries with keys order_id (stripped string) and quantity (int), in input order. A valid header with no data returns an empty list.']),
('Discount and shipping in integer cents',[
'items is a list of two-element tuples or lists (unit_price_cents, quantity). Both fields must be nonnegative built-in ints. discount_percent must be a built-in int from 0 through 100; shipping and free_shipping_threshold must be nonnegative built-in ints. Booleans are invalid in every integer field. Other input shapes are guaranteed.',
'Validate all integer fields and raise ValueError for invalid values, including discount/shipping/threshold arguments when items is empty. Preserve items.',
'Compute subtotal as the sum of unit_price_cents * quantity. Compute discounted subtotal by exact integer arithmetic, rounding subtotal * (100 - discount_percent) / 100 down to whole cents.',
'Shipping is free if the pre-discount subtotal is at least free_shipping_threshold; otherwise add shipping. For empty items, return 0 after validation regardless of shipping or threshold. Return an integer total.'])]

def main():
    DEST.mkdir(exist_ok=True)
    originals=[json.loads(line) for line in (EXP/'requirements.jsonl').read_text().splitlines()]
    audit=json.loads((EXP/'task-audit.json').read_text())
    tasks=[]
    for old,(title,clauses),meta in zip(originals,CONTRACTS,audit['tasks'],strict=True):
        prompt='Write tests before implementation for this requirement.\n\nPublic API:\nfrom solution import '+old['signature'].split('(')[0]+'\n'+old['signature']+'\n\nAcceptance criteria:\n'+'\n'.join(f'{i}. {text}' for i,text in enumerate(clauses,1))
        task=dict(id=old['id'],title=title,revision='questions-v02',messages=[dict(role='system',content=SYSTEM),dict(role='user',content=prompt)],acceptance_criteria=clauses,metadata=dict(split='evaluation-development-only; never SFT training',provenance='assistant-authored synthetic requirement; revised for clarity; owner approval pending',domain=meta['domain'],dependency_level=meta['dependency_level'],context='requirement plus agreed public interface; no implementation',paper_context_tier='not applicable: paper tiers describe function-to-test inputs',target_skills=meta['target_behaviors'],programming_language='Python',framework='pytest',allowed_dependencies=['pytest','Python standard library'],teacher_reasoning_status='not authored',teacher_tests_status='not authored',semantic_validation='reference smoke checks only; revised contract approval pending',test_complexity='not measured: no approved teacher tests',oracle_quality='pending test generation and review',smell_quality='pending test generation and review'))
        task['prompt_sha256']=hashlib.sha256(json.dumps(task['messages'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        tasks.append(task)
    content=''.join(json.dumps(t,ensure_ascii=False)+'\n' for t in tasks)
    path=DEST/'requirements.jsonl'
    if path.exists() and path.read_text()!=content:raise RuntimeError('Version already exists with different content; create another revision')
    path.write_text(content)
    env=dict(line.split('=',1) for line in (DOMAIN/'review/.env').read_text().splitlines() if line and not line.startswith('#'))
    client=rg.Argilla(api_url='http://127.0.0.1:7900',api_key=env['ARGILLA_API_KEY'])
    name='thinking-tdd-questions-v02'
    dataset=client.datasets(name=name,workspace=env['ARGILLA_WORKSPACE'])
    if dataset is None:
        settings=rg.Settings(guidelines='Review the question, not a generated answer. These ten tasks are evaluation/development only and will never enter SFT training. No approved teacher reasoning or tests exist yet. Approve whether the requirement is clear, solvable and suitable for writing tests before implementation; note missing decisions. The API only fixes how future code and tests will connect. Old baseline failures and execution logs are deliberately excluded. Later SFT examples will be separate and execution-verified. This small set is L0/L1 only, not balanced across every dependency/context level in the paper.',fields=[rg.TextField(name=n,title=t,use_markdown=True) for n,t in [('purpose','What you are reviewing'),('system','Shared system instruction — seen by the model'),('question','Full question — seen by the model'),('metadata','Diversity and validation metadata — NOT model input')]],questions=[rg.LabelQuestion(name='approval',title='Can this requirement be used for the demo evaluation?',labels=['approve','revise','reject','uncertain'],required=True),rg.LabelQuestion(name='clarity',title='Are inputs, outputs and expected behavior sufficiently specified?',labels=['clear','minor-clarification','ambiguous'],required=True),rg.TextQuestion(name='changes',title='Requested changes or missing behavior',required=False)])
        dataset=rg.Dataset(name=name,workspace=env['ARGILLA_WORKSPACE'],settings=settings,client=client);dataset.create()
    existing={str(r.id) for r in dataset.records(with_responses=False,with_suggestions=False)}
    records=[]
    for task in tasks:
        rid=str(uuid.uuid5(uuid.NAMESPACE_URL,'thinking-tdd-questions-v02/'+task['id']))
        if rid not in existing:
            records.append(rg.Record(id=rid,fields=dict(purpose='**'+task['title']+'**\n\nQuestion approval only. This is not an SFT training example. Correct teacher reasoning and tests will be authored separately for different tasks.',system=task['messages'][0]['content'],question=task['messages'][1]['content'],metadata='```json\n'+json.dumps(task['metadata'],indent=2)+'\n```')))
    if records:dataset.records.log(records)
    count=sum(1 for _ in dataset.records(with_responses=False,with_suggestions=False))
    assert count==10,count
    receipt=dict(dataset=name,dataset_id=str(dataset.id),records=count,url=f'http://127.0.0.1:7900/dataset/{dataset.id}/annotation-mode',questions_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),human_approval_submitted=False)
    (DEST/'review-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
