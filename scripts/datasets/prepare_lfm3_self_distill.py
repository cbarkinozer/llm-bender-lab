"""exp-016 data steps: English prompts for self-generation, then the self-distilled training file.

prompts: write the 160 English-task prompts (one per group, from exp014's frozen data) for LFM3 to answer itself.
build:   combine LFM3's own answers (generate_lfm3_self_targets.py) with Turkish renderings of the final answers
         into a file in exactly exp014's prompt/completion format, rows and order unchanged.
Row order in exp014 data: groups of four = tr->tr, en->tr, tr->en, en->en.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'evaluation'))
import lfm3_eval_v2_scoring as scoring  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
EXP = BASE / 'exp-016-self-distill-targets'
SOURCE = BASE / 'cookbook-sft-v01/train.jsonl'
SOURCE_SHA256 = 'fc4b679256de703d0606d300b8c8e6fc4d128e848eddc2635a2da4ab8efe10e9'
DIRECTIONS = ['tr->tr', 'en->tr', 'tr->en', 'en->en']
DROP_GROUPS = {'g119'}  # 4178 tokens with its own reasoning, over exp014's max_length of 4096 (measured on the pod)
MAX_ANSWER_CHARS = 1500  # writer-cost cap; also keeps lengths near exp014's mean (733 characters)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_rows():
    assert sha256(SOURCE) == SOURCE_SHA256, 'exp014 source data changed'
    rows = [json.loads(s) for s in SOURCE.read_text(encoding='utf-8').splitlines()]
    assert len(rows) == 640
    return rows


def prompts():
    rows = source_rows()
    out = []
    for g in range(160):
        quad = rows[4 * g:4 * g + 4]
        row = quad[3]  # en->en: English system, English task, "Answer in English."
        assert row['prompt'][0]['content'].startswith('You are'), g  # English system prompt, English-output task
        flags = {r['chat_template_kwargs']['enable_thinking'] for r in quad}
        assert len(flags) == 1, f'group {g} mixes thinking modes'
        out.append(dict(id=f'g{g:03d}', messages=row['prompt'], thinking=flags.pop()))
    path = EXP / 'data-local/en-prompts.jsonl'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in out), encoding='utf-8', newline='\n')
    print('wrote', path, len(out), 'thinking groups', sum(r['thinking'] for r in out))


def split_answer(raw, thinking):
    text, closed = scoring.split_thinking(raw, thinking)
    if thinking and not closed:
        return None, None
    reasoning = None
    if thinking:
        reasoning = raw.replace('<|im_end|>', '').rsplit(scoring.THINK_CLOSE, 1)[0].strip()
    return reasoning, text


def invariants(en, tr):
    """Numbers, code spans and URLs of the English answer must reappear in the Turkish rendering."""
    problems = []
    en_numbers = scoring_numbers(en, 'en')
    tr_numbers = scoring_numbers(tr, 'tr')
    if en_numbers - tr_numbers:
        problems.append(f'numbers missing in Turkish: {sorted(map(str, en_numbers - tr_numbers))}')
    fenced = re.findall(r'```.*?```', en, re.S)
    inline = re.findall(r'(?<!`)`[^`\n]+`(?!`)', re.sub(r'```.*?```', '', en, flags=re.S))
    for span in fenced + inline + re.findall(r'https?://\S+', en):
        if span not in tr:
            problems.append(f'span not preserved: {span}')
    return problems


def scoring_numbers(text, lang):
    values = set()
    for token in re.findall(r'\d[\d.,]*\d|\d', text):
        value = scoring.parse_number(token, lang)
        if value is not None:
            values.add(value.normalize())
    return values


def choose(record, thinking):
    """Shortest complete (EOS) sample with a usable answer; None if the model never finished."""
    best = None
    for index, sample in enumerate(record['samples']):
        if sample['finish_reason'] != 'eos':
            continue
        reasoning, answer = split_answer(sample['raw_output'], thinking)
        if answer and (best is None or len(answer) < len(best[2])):
            best = (index, reasoning, answer)
    if best is not None and len(best[2]) > MAX_ANSWER_CHARS:
        return None
    return best


def english_answers():
    """Write the chosen English answer per group so Turkish renderings can be written against it."""
    rows = source_rows()
    gen = {json.loads(s)['id']: json.loads(s) for s in (EXP / 'data-local/generated.jsonl').read_text(encoding='utf-8').splitlines()}
    chosen, dropped = [], []
    for g in range(160):
        gid = f'g{g:03d}'
        thinking = rows[4 * g]['chat_template_kwargs']['enable_thinking']
        best = choose(gen[gid], thinking)
        if best is None:
            dropped.append(gid)
        else:
            chosen.append(dict(id=gid, sample=best[0], answer=best[2]))
    (EXP / 'data-local/en-answers.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in chosen),
                                                    encoding='utf-8', newline='\n')
    print('chosen', len(chosen), 'dropped (no complete own answer)', dropped)


def build(translations):
    rows = source_rows()
    gen = {json.loads(s)['id']: json.loads(s) for s in (EXP / 'data-local/generated.jsonl').read_text(encoding='utf-8').splitlines()}
    tr = {json.loads(s)['id']: json.loads(s) for s in Path(translations).read_text(encoding='utf-8').splitlines()}
    out, positions = [], {}
    report: dict = dict(groups=160, dropped_groups=[], invariant_problems={}, chosen_sample={})
    for g in range(160):
        gid = f'g{g:03d}'
        quad = rows[4 * g:4 * g + 4]
        thinking = quad[0]['chat_template_kwargs']['enable_thinking']
        best = None if gid in DROP_GROUPS else choose(gen[gid], thinking)
        if best is None:
            report['dropped_groups'].append(gid)
            continue
        index, reasoning, answer = best
        report['chosen_sample'][gid] = index
        turkish = tr[gid]['answer_tr'].strip()
        problems = invariants(answer, turkish)
        if problems:
            report['invariant_problems'][gid] = problems
        for direction, row, source_index in zip(DIRECTIONS, quad, range(4 * g, 4 * g + 4)):
            target = turkish if direction.endswith('tr') else answer
            completion = dict(role='assistant', content=target if target.endswith('\n') else target + '\n')
            if thinking:
                completion['thinking'] = reasoning
            positions[source_index] = len(out)
            out.append(dict(prompt=row['prompt'], completion=[completion], chat_template_kwargs=row['chat_template_kwargs']))
    if report['invariant_problems']:
        raise SystemExit('Turkish rendering invariants failed:\n' + json.dumps(report['invariant_problems'], ensure_ascii=False, indent=1))
    order_b = json.loads((BASE / 'bilingual-pilot-v01/revisions/v01-corrections-02/token-budget-and-order.json').read_text(encoding='utf-8'))['order_b']
    filtered = [positions[i] for i in order_b if i in positions]
    # exp014 consumed the first 552 of order_b over 640 rows; keep the same exposure per row
    order = filtered[:(552 * len(out) // 640) // 8 * 8]
    assert len(order) % 8 == 0 and len(order) >= 8, len(order)
    path = EXP / 'train-selfdistill.jsonl'
    blob = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in out).encode('utf-8')
    if path.exists() and path.read_bytes() != blob:
        raise SystemExit('Refusing to change a frozen training file')
    path.write_bytes(blob)
    report.update(rows=len(out), sha256=hashlib.sha256(blob).hexdigest(), order_note='exp012 order_b filtered to kept groups; first 552*rows/640 entries rounded down to a multiple of 8 (same exposure per row as exp014)')
    (EXP / 'order.json').write_text(json.dumps(order) + '\n', encoding='utf-8')
    (EXP / 'build-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('wrote', path, len(out), 'rows;', len(report['dropped_groups']), 'groups dropped')


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('prompts')
    sub.add_parser('answers')
    b = sub.add_parser('build')
    b.add_argument('--translations', required=True)
    args = parser.parse_args()
    if args.command == 'prompts':
        prompts()
    elif args.command == 'answers':
        english_answers()
    else:
        build(args.translations)


if __name__ == '__main__':
    main()
