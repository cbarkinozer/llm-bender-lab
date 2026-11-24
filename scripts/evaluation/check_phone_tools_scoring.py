"""Self-check of the phone-tools scorer on the pinned dataset: gold against gold, perturbations, and render-parse round trip.

Run on CPU, no model weights needed (the tokenizer only):
    python scripts/evaluation/check_phone_tools_scoring.py [--out report.json]
Exit code 1 when a check fails.
"""
import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phone_tools_scoring as S  # noqa: E402

DATASET = 'LiquidAI/phone-assistant-tools'
DATASET_REVISION = '02100f57ab94eda248909b83a79e9d46a590d038'
MODEL = 'LiquidAI/LFM3-1.7B'
MODEL_REVISION = '0dc4268b561499c648c7ba7c9466bf3d8d01517a'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download
    from transformers import AutoTokenizer

    def get(name):
        return hf_hub_download(DATASET, name, repo_type='dataset', revision=DATASET_REVISION)

    tools = json.loads(Path(get('tools.json')).read_text(encoding='utf-8'))
    kinds = json.loads(Path(get('scoring.json')).read_text(encoding='utf-8'))
    scorer = S.Scorer(tools, kinds)
    report, failures = {}, []

    # 1. gold against gold, and a wrong tool name must fail
    for split in ('train', 'test', 'test_unseen', 'showcase'):
        rows = pq.read_table(get(f'{split}.parquet')).to_pylist()
        ok = bad_self = bad_name = 0
        for r in rows:
            gold = json.loads(r['calls'])
            ok += scorer.calls_match(gold, gold)
            if gold:
                wrong = copy.deepcopy(gold)
                wrong[0]['name'] = 'definitely_not_a_tool'
                bad_name += scorer.calls_match(gold, wrong)
            else:
                bad_self += scorer.calls_match(gold, [{'name': tools[0]['function']['name'], 'arguments': {}}])
        report[split] = dict(rows=len(rows), gold_match=ok, wrong_name_accepted=bad_name, call_on_no_call_accepted=bad_self)
        if ok != len(rows) or bad_name or bad_self:
            failures.append(f'{split}: {report[split]}')

    # 2. unit checks on perturbations of the comparators
    c = S.COMPARE
    cases = [('time', '19:00', '19:00:00', True), ('time', '9:05', '09:05', True), ('time', '19:00', '19:01', False),
             ('date', '2026-12-03', '2026-12-03', True), ('date', '2026-12-03', '03/12/2026', False),
             ('datetime', '2026-12-03T19:00', '2026-12-03 19:00:00', True),
             ('name', 'José Álvarez', 'jose alvarez', True), ('name', 'Anna Smith', 'Smith Anna', True),
             ('name', 'Anna Smith', 'Bob Jones', False), ('code', '+90 532 123 45 67', '+905321234567', True),
             ('code', 'USD', 'EUR', False), ('enum', 'high', ' High ', True), ('enum', 'high', 'low', False),
             ('bool', True, 1, False), ('bool', True, True, True), ('int', 5, 5.0, True), ('int', 5, True, False),
             ('number', 2.5, '2.5', False), ('expr', '2+3*4', '14', True), ('expr', '2^3', '8', True), ('expr', '1/0', '1', False),
             ('expr', '9**999', '1', False), ('text', 'Call mom tonight', 'call mom tonight!', True),
             ('text', 'Call mom tonight', 'Buy milk', False), ('list_enum', ['a', 'b'], ['B', 'A'], True),
             ('list_enum', ['a'], 'a', False), ('list_name', ['Ann', 'Bob'], ['bob', 'ann'], True),
             ('list_text', ['x y'], ['x y', 'z'], False)]
    unit = []
    for kind, g, p, expected in cases:
        got = bool(c[kind](g, p))
        if got != expected:
            unit.append(f'{kind}: {g!r} vs {p!r} -> {got}, expected {expected}')
    report['unit_cases'] = dict(total=len(cases), failed=unit)
    failures += unit

    # 3. the chat template renders gold calls and parse_response reads them back (all training rows)
    tok = AutoTokenizer.from_pretrained(MODEL, revision=MODEL_REVISION, trust_remote_code=True, padding_side='left')
    msgs = [{'role': 'system', 'content': 'x'}, {'role': 'user', 'content': 'y'}]
    prompt = tok.apply_chat_template(msgs, tools=tools, add_generation_prompt=True, tokenize=False, enable_thinking=False)
    rows = [r for s in ('train', 'test', 'test_unseen') for r in pq.read_table(get(f'{s}.parquet')).to_pylist()]
    trips = fails = 0
    for r in rows:
        gold = json.loads(r['calls'])
        if not gold:
            continue
        full = tok.apply_chat_template(msgs + [{'role': 'assistant', 'content': '', 'tool_calls': [{'type': 'function', 'function': g} for g in gold]}],
                                       tools=tools, tokenize=False, enable_thinking=False)
        assert full.startswith(prompt), 'rendered conversation does not extend the generation prompt'
        ids = tok(full[len(prompt):], add_special_tokens=False).input_ids
        parsed = tok.parse_response(ids, prefix=prompt, tools=tools)
        pred = [x['function'] for x in parsed.get('tool_calls') or []]
        trips += 1
        if not scorer.calls_match(gold, pred):
            fails += 1
            if fails <= 5:
                failures.append(f'round trip {r["id"]}: {json.dumps(gold, ensure_ascii=False)[:200]} -> {json.dumps(pred, ensure_ascii=False)[:200]}')
    report['round_trip'] = dict(rows=trips, failed=fails)
    if fails:
        failures.append(f'round trip failed for {fails} of {trips} rows')
    report['prompt_tokens'] = len(tok(prompt, add_special_tokens=False).input_ids)
    report['failures'] = failures
    print(json.dumps(report, ensure_ascii=False, indent=1))
    if args.out:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
