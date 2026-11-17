"""Validate the bilingual pilot dataset and write machine-readable reports under bilingual-pilot-v01/validation/.

Checks: counts, schema, ids, TR->TR traceability, duplicates, number/unit parity, structural parity, constraint checks,
independent arithmetic verification, reasoning/final separation, heuristic language ID, native-template token statistics
with the pinned local LFM3 tokenizer (renderer verified byte-exact against the historical label audit).

  python scripts/datasets/validate_lfm3_bilingual_pilot.py
Errors make the process exit non-zero; warnings require review and are listed in the report.
"""
import collections
import datetime
import itertools
import json
import math
import re
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bilingual_pilot_common import (BASE, DIRECTIONS, INSTRUCTION, PILOT, SYSTEM, SYSTEM_TR, instruction_for, json_bytes, normalized,
                                    read_jsonl, sha256_file, sha256_text, with_instruction)

OUT = PILOT / 'validation'
TOKENIZER = BASE / 'base-sft160-runtime-local/tokenizer/tokenizer.json'
HISTORICAL_AUDIT = BASE / 'pilot160-runtime-local/label-audit.json'
HISTORICAL_TOKENIZED = BASE / 'pilot160-runtime-local/train-tokenized.jsonl'
MAX_LENGTH = 4096
BOS = '<|startoftext|>'
REQUIRED = ['id', 'group_id', 'canonical_task_id', 'split', 'direction', 'input_language', 'output_language', 'messages',
            'worked_solution', 'has_reasoning', 'category', 'source_key', 'language_instruction', 'source_row_id',
            'original_source', 'original_row_sha256', 'transformation', 'generation_method', 'output_language_effect']
FORBIDDEN_TAGS = ['<think>', '</think>', '<thinking>', '</thinking>', '<|im_start|>', '<|im_end|>', '<|startoftext|>']

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


# ---------------------------------------------------------------- numbers
TR_NUM = re.compile(r'\d+(?:\.\d{3})*(?:,\d+)?')
EN_NUM = re.compile(r'\d+(?:,\d{3})*(?:\.\d+)?')


def number_multiset(text, lang):
    pattern = TR_NUM if lang == 'tr' else EN_NUM
    out = collections.Counter()
    for tok in pattern.findall(text):
        tok = tok.replace('.', '').replace(',', '.') if lang == 'tr' else tok.replace(',', '')
        out[str(Decimal(tok).normalize())] += 1
    return out


# ---------------------------------------------------------------- structure
def structure(text):
    lines = text.split('\n')
    return dict(paragraphs=len([p for p in re.split(r'\n\s*\n', text) if p.strip()]),
                bullets=sum(bool(re.match(r'\s*[*\-•]\s', l)) for l in lines),
                numbered=sum(bool(re.match(r'\s*\d+[.)]\s', l)) for l in lines),
                table_rows=sum(l.strip().startswith('|') for l in lines),
                headings=sum(l.startswith('#') for l in lines),
                code_fences=text.count('```'))


# ---------------------------------------------------------------- language heuristics
TR_WORDS = set('ve bir bu için ile de da ama çok olarak daha gibi veya ancak çünkü kadar sonra olan her bunu şu o ne mi mı mu mü değil var yok olur olması'.split())
EN_WORDS = set('the and of to in is a for that with as are on be this it by or an at from not can will which but have has was you your their its'.split())


def lang_score(text):
    toks = re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü']+", text.lower())
    if not toks:
        return 0.0, 0.0
    tr = sum(t in TR_WORDS for t in toks) / len(toks)
    en = sum(t in EN_WORDS for t in toks) / len(toks)
    return tr, en


# ---------------------------------------------------------------- arithmetic
def C(n, k):
    return math.comb(n, k)


def arith_checks():
    """group -> (computed dict, numbers (as normalized strings) that must appear among assistant+reasoning numbers)"""
    F = Fraction
    out = {}
    out['g013'] = (dict(loss=5000 - 3200, loss_pct=F(5000 - 3200, 5000) * 100, y_gain=4725 - 4500,
                        y_pct=F(4725 - 4500, 4500) * 100, gap=36 + 5), ['1800', '36', '225', '5', '41'])
    out['g014'] = (dict(ex_vat=F(450) / F(8, 10), incl=F(450) / F(8, 10) * F(12, 10), vat=F(450) / F(8, 10) * F(2, 10)),
                   ['562.5', '675', '112.5'])
    out['g016'] = (dict(total=3 * 12, done=2 * 6, rest=36 - 12, check=36 * F(2, 3)), ['36', '12', '24'])
    out['g021'] = (dict(interest=8000 * F(1, 10), three_years=8000 * F(1, 10) * 3, total=8000 + 2400), ['800', '2400', '10400'])
    h, v = F(1, 2) * F(98, 10) * F(18, 10) ** 2, F(98, 10) * F(18, 10)
    out['g023'] = (dict(h=float(h), v=float(v), E_kJ=float(F(1, 2) * 600 * v * v) / 1000), ['15.9', '17.6', '93'])
    out['g025'] = (dict(reps=3 * 4 * 3 * 12, seconds=F(3 * 4 * 3 * 12) * F(54, 10), minutes=F(3 * 4 * 3 * 12) * F(54, 10) / 60),
                   ['432', '2332.8', '38.88'])
    out['g026'] = (dict(work=50 * F(42, 10), rest=4 * 60, move=50 * F(42, 10) + 240, five=5 * (50 * F(42, 10) + 240),
                        total=5 * (50 * F(42, 10) + 240) + 4 * 90, minutes=(5 * (50 * F(42, 10) + 240) + 360) / 60),
                   ['210', '240', '450', '2250', '360', '2610', '43.5'])
    km = 260 + 300 + 480
    fuel = F(km) * F(6, 100)
    out['g028'] = (dict(km=km, fuel=fuel, refuel=fuel - 50, konya_price=45 * F(96, 100), antalya_price=45 * F(92, 100),
                        konya_cost=(fuel - 50) * 45 * F(96, 100), antalya_cost=(fuel - 50) * 45 * F(92, 100),
                        tank_after_refuel=(50 - F(260) * F(6, 100)) + (fuel - 50), needed=F(300) * F(6, 100) + F(480) * F(6, 100)),
                   ['1040', '62.4', '12.4', '535.68', '513.36', '46.8'])
    x = F(15, 2); y = (50 - 3 * x) / 2
    out['g031'] = (dict(x=x, y=y, ali=3 * x + 2 * y, ayse=2 * x + 4 * y), ['7.5', '13.75', '50', '70'])
    out['g036'] = (dict(below=90 * (1 - F(3, 10) - F(5, 10))), ['18'])
    out['g037'] = (dict(two_pair=C(13, 2) * C(4, 2) ** 2 * C(11, 1) * C(4, 1), flush=C(13, 5) * 4, deck=C(52, 5),
                        p2=F(C(13, 2) * C(4, 2) ** 2 * 11 * 4, C(52, 5)) * 100, pf=F(C(13, 5) * 4, C(52, 5)) * 100,
                        ratio=F(C(13, 2) * C(4, 2) ** 2 * 11 * 4, C(13, 5) * 4)), ['123552', '5148', '2598960', '4.75', '0.198', '24'])
    out['g038'] = (dict(t=F(12, 1000) * 64), ['0.768'])
    out['g076'] = (dict(year=2 * 150 * 52), ['15600'])
    dx, dy = 3 * math.cos(math.pi / 4) - 2, 4 - 3 * math.sin(math.pi / 4)
    out['g082'] = (dict(dx=dx, dy=dy, d=math.hypot(dx, dy), theta=math.degrees(math.atan2(dx, dy))), ['0.121', '1.879', '1.88', '3.7'])
    out['g084'] = (dict(x=-2, left=3 * (-2 + 4), right=2 * -2 + 10), ['2', '6'])
    out['g104'] = (dict(month=F(7200, 12), allowance=F(7200, 12) / F(4, 10), year=F(7200, 12) / F(4, 10) * 12,
                        left=F(7200, 12) / F(4, 10) - F(7200, 12)), ['600', '1500', '18000', '900'])
    out['g108'] = (dict(gross=20 * 15000, discount=20 * 15000 * F(1, 10), net=20 * 15000 * F(9, 10)), ['300000', '30000', '270000'])
    A = F(60); R = 100 - A
    out['g109'] = (dict(A=A, R=R, value=200 * A + 150 * R, target=180 * 100), ['60', '40', '18000'])
    out['g116'] = (dict(slices=8 * 12, guests=96 // 2), ['96', '48'])
    out['g118'] = (dict(month=8 * 175 * 5 * 4, left=8 * 175 * 5 * 4 * F(3, 4)), ['28000', '21000'])
    best = max(((s, c, b) for s in (0, 1) for c in (0, 1) for b in range(0, 10)
                if s * 250 + c * 180 + b * 70 <= 600 and s * 28 + c * 12 + b * 3 >= 20),
               key=lambda t: (t[0] * 28 + t[1] * 12 + t[2] * 3, -(t[0] * 250 + t[1] * 180 + t[2] * 70)))
    out['g120'] = (dict(best=best, kcal=best[0] * 250 + best[1] * 180 + best[2] * 70, protein=best[0] * 28 + best[1] * 12 + best[2] * 3),
                   ['570', '46', '430', '40'])
    out['g127'] = (dict(interest=4000 * F(1, 10) * 3, pct=F(4000 * 3, 10 * 4000) * 100), ['1200', '30'])
    out['g129'] = (dict(n=next(n for n in range(1, 20) if 4 ** (n - 1) == 1024)), ['1024', '6'])
    out['g131'] = (dict(hours=F(240, 60)), ['4'])
    out['g136'] = (dict(extra=80 - F(120, 2)), ['60', '80', '20'])
    out['g138'] = (dict(left=12 - (4 + 2 + 3), rule_cap=2 + 3), ['9', '3', '5', '12'])
    out['g140'] = (dict(n=2000 * F(4, 10)), ['800'])
    out['g148'] = (dict(diff=50 - 45), ['50', '45', '5'])
    worst = max(1 + (math.floor(math.log2(n)) if n else 0) for n in [4096])
    out['g150'] = (dict(worst=worst), ['4096', '12', '13'])
    t = datetime.datetime(2026, 1, 1, 4, 0) + datetime.timedelta(hours=2 + 6 + 3 + 6 + 2, minutes=30 + 15 + 45)
    out['g151'] = (dict(total_h=F(20 * 60 + 30, 60), arrival_utc=t.strftime('%H:%M'), tehran=(t + datetime.timedelta(hours=3, minutes=30)).strftime('%H:%M')),
                   ['20', '30', '4'])
    out['g153'] = (dict(top=F(607) / F(24, 10), bottom=F(607) * F(14, 10) / F(24, 10),
                        implied_density=(F(1012, 1000) + F(14, 10) * F(1025, 1000)) / F(24, 10),
                        stated_density=F(1012, 1000) * F(1007, 1000)), ['252.92', '354.08'])
    out['g156'] = (dict(floor=20 + 15 + 10, extra=(60 - 45) / 3, per=(25, 20, 15), weekly=(75, 60, 45)), ['45', '15', '25', '20', '75', '60'])
    return out


def pct(values, p):
    values = sorted(values)
    if not values:
        return None
    return values[min(len(values) - 1, max(0, math.ceil(p / 100 * len(values)) - 1))]


def dist(values):
    return dict(n=len(values), min=min(values) if values else None, median=pct(values, 50), p90=pct(values, 90),
                p95=pct(values, 95), p99=pct(values, 99), max=max(values) if values else None,
                total=sum(values))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    train = read_jsonl(PILOT / 'data/train.jsonl')
    originals = {r['group_id']: r for r in read_jsonl(PILOT / 'data/source-originals.jsonl')}
    source_rows = read_jsonl(BASE / 'sft-pilot160-v01/train.jsonl')
    by_group = collections.defaultdict(dict)
    for r in train:
        by_group[r['group_id']][r['direction']] = r
    report = dict(inputs={'train.jsonl': sha256_file(PILOT / 'data/train.jsonl'),
                          'source-originals.jsonl': sha256_file(PILOT / 'data/source-originals.jsonl')})

    # ---- counts, schema, ids
    if len(train) != 640:
        err(f'rows {len(train)} != 640')
    if len(by_group) != 160:
        err(f'task groups {len(by_group)} != 160')
    per_dir = collections.Counter(r['direction'] for r in train)
    if set(per_dir) != set(DIRECTIONS) or any(v != 160 for v in per_dir.values()):
        err(f'per direction {dict(per_dir)}')
    if len({r['id'] for r in train}) != 640:
        err('duplicate row ids')
    for g, d in by_group.items():
        if set(d) != set(DIRECTIONS):
            err(f'{g} directions {sorted(d)}')
        if len({r['split'] for r in d.values()}) != 1:
            err(f'{g} spans multiple splits')
    schema_problems = 0
    for r in train:
        miss = [k for k in REQUIRED if k not in r]
        if miss:
            err(f"{r['id']}: missing {miss}")
            schema_problems += 1
        roles = [m['role'] for m in r['messages']]
        if roles != ['system', 'user', 'assistant']:
            err(f"{r['id']}: roles {roles}")
        if any(not m['content'].strip() for m in r['messages']):
            err(f"{r['id']}: empty message")
        if r['has_reasoning'] != bool(r['worked_solution']):
            err(f"{r['id']}: has_reasoning mismatch")
        variant, expected = instruction_for(r['group_id'].split('-')[1], r['input_language'], r['output_language'])
        if r['language_instruction'].get('variant') != variant:
            err(f"{r['id']}: instruction variant mismatch")
        if r['language_instruction']['text'] != expected or not r['messages'][1]['content'].rstrip().endswith(expected):
            err(f"{r['id']}: language instruction not appended consistently")
        if r['messages'][0]['content'] != SYSTEM[r['input_language']]:
            err(f"{r['id']}: system prompt not language-matched")
        for text in [m['content'] for m in r['messages']] + ([r['worked_solution']] if r['worked_solution'] else []):
            for tag in FORBIDDEN_TAGS:
                if tag in text:
                    err(f"{r['id']}: forbidden tag {tag}")
    report['counts'] = dict(rows=len(train), groups=len(by_group), per_direction=dict(per_dir), schema_problem_rows=schema_problems)

    # ---- TR->TR traceability and unchanged originals
    trace = dict(checked=0, identical=0)
    for g, d in by_group.items():
        o = originals[g]
        row = d['tr-tr']
        src_idx = int(g.split('g')[-1]) - 1
        src = source_rows[src_idx]
        trace['checked'] += 1
        sys_ok = row['messages'][0]['content'] == o['system'] == src['messages'][0]['content'] == SYSTEM_TR
        user_ok = row['messages'][1]['content'] == with_instruction(src['messages'][1]['content'], 'tr', 'tr')
        asst_ok = row['messages'][2]['content'] == src['messages'][2]['content'] == o['assistant']
        ws_ok = row['worked_solution'] == src['worked_solution'] == o['worked_solution']
        hashes_ok = (sha256_text(src['messages'][1]['content']) == o['source_user_sha256'] == row['source_user_sha256'] and
                     sha256_text(src['messages'][2]['content']) == o['source_assistant_sha256'] == row['source_assistant_sha256'])
        if sys_ok and user_ok and asst_ok and ws_ok and hashes_ok and row['source_row_id'] == src['id']:
            trace['identical'] += 1
        else:
            err(f'{g}: TR->TR row not traceable/unchanged (sys={sys_ok} user={user_ok} asst={asst_ok} ws={ws_ok} hash={hashes_ok})')
    report['tr_tr_traceability'] = trace

    # ---- duplicates
    norm_user = collections.defaultdict(list)
    norm_asst = collections.defaultdict(list)
    for r in train:
        norm_user[normalized(r['messages'][1]['content'])].append(r['id'])
        norm_asst[normalized(r['messages'][2]['content'])].append(r['id'])
    dup_users = {k[:60]: v for k, v in norm_user.items() if len(v) > 1}
    if dup_users:
        err(f'duplicate normalized user prompts: {list(dup_users.values())[:5]}')
    dup_asst = [v for v in norm_asst.values() if len(v) > 1]
    unexpected, by_design = [], []
    for ids in dup_asst:
        groups = {i.split('-')[1] for i in ids}
        rows_ = [next(r for r in train if r['id'] == i) for i in ids]
        # By design the two input languages of one group share the output-language target, and language-bound or
        # language-neutral groups share one target across both output languages.
        same_group = len(groups) == 1
        (by_design if same_group else unexpected).append(ids)
        if same_group and len({r['output_language'] for r in rows_}) > 1 and not all(r['output_language_effect'] != 'full' or r['output_language'] == 'tr' for r in rows_):
            err(f'cross-output-language duplicate target not flagged as language-bound: {ids}')
    if unexpected:
        err(f'unexpected duplicate assistant texts across task groups: {unexpected[:5]}')
    report['duplicates'] = dict(duplicate_normalized_user_prompts=len(dup_users), duplicate_assistant_text_sets=len(dup_asst),
                                by_design_same_group_sets=len(by_design), unexpected_sets=len(unexpected),
                                note='By design the two input languages of a group share the same output-language target text.')

    # ---- cross-direction consistency: the four rows of a group reuse identical underlying text
    cross = 0
    for g, d in by_group.items():
        def base(r):
            u = r['messages'][1]['content']
            return u[:len(u) - len(r['language_instruction']['text'])].rstrip()
        ok = (base(d['tr-tr']) == base(d['tr-en']) and base(d['en-tr']) == base(d['en-en']) and
              d['tr-tr']['messages'][2]['content'] == d['en-tr']['messages'][2]['content'] and
              d['tr-en']['messages'][2]['content'] == d['en-en']['messages'][2]['content'] and
              d['tr-tr']['worked_solution'] == d['en-tr']['worked_solution'] and
              d['tr-en']['worked_solution'] == d['en-en']['worked_solution'])
        cross += int(ok)
        if not ok:
            err(f'{g}: directions do not reuse identical underlying input/output text')
    report['cross_direction_consistency_groups_ok'] = cross
    en_equals_tr_user = [g for g, d in by_group.items() if normalized(d['tr-tr']['messages'][1]['content']) == normalized(d['en-en']['messages'][1]['content'])]
    report['duplicates']['en_user_identical_to_tr_user_groups'] = en_equals_tr_user

    # ---- output-language effect census
    census = collections.Counter(r['output_language_effect'] for r in train if r['output_language'] == 'en')
    report['en_output_language_effect'] = dict(census)
    report['en_output_language_effect_neutral_groups'] = sorted(r['group_id'] for r in train if r['direction'] == 'tr-en' and r['output_language_effect'] == 'neutral_content')
    report['en_output_language_effect_preserve_groups'] = sorted(r['group_id'] for r in train if r['direction'] == 'tr-en' and r['output_language_effect'] == 'preserve_turkish_object')

    # ---- reasoning/final separation
    sep = dict(reasoning_rows_per_direction={d: sum(1 for r in train if r['direction'] == d and r['has_reasoning']) for d in DIRECTIONS},
               reasoning_equals_final=0, final_contains_reasoning=0, reasoning_without_source=0, source_reasoning_missing=0)
    for r in train:
        o = originals[r['group_id']]
        if r['has_reasoning'] != bool(o['worked_solution']):
            sep['source_reasoning_missing' if not r['has_reasoning'] else 'reasoning_without_source'] += 1
            err(f"{r['id']}: reasoning presence differs from original")
        if r['worked_solution']:
            final = r['messages'][2]['content']
            if r['worked_solution'].strip() == final.strip():
                sep['reasoning_equals_final'] += 1
                err(f"{r['id']}: reasoning equals final answer")
            if r['worked_solution'].strip() in final:
                sep['final_contains_reasoning'] += 1
                err(f"{r['id']}: final contains whole reasoning")
    report['reasoning_separation'] = sep

    # ---- number parity TR vs EN (reviewed exceptions recorded separately)
    parity = []
    for g, d in by_group.items():
        o = originals[g]
        en_row = d['tr-en']
        en_user = d['en-tr']['messages'][1]['content']
        en_user_base = en_user[:len(en_user) - len(INSTRUCTION[('en', 'tr')])].rstrip()
        pairs = [('user', o['user'], en_user_base), ('assistant', o['assistant'], en_row['messages'][2]['content'])]
        if o['worked_solution']:
            pairs.append(('reasoning', o['worked_solution'], en_row['worked_solution']))
        for field, tr_text, en_text in pairs:
            a, b = number_multiset(tr_text, 'tr'), number_multiset(en_text, 'en')
            if a != b:
                parity.append(dict(group=g, field=field, only_tr=dict(a - b), only_en=dict(b - a)))
    exc = json.loads((OUT / 'reviewed-exceptions.json').read_text(encoding='utf-8'))
    reviewed = {(e['group'], e['field']) for e in exc['number_parity']}
    for p_ in parity:
        if (p_['group'], p_['field']) not in reviewed:
            err(f'unreviewed number parity mismatch {p_}')
    report['number_parity_mismatches'] = len(parity)
    report['number_parity_unreviewed'] = sum((p_['group'], p_['field']) not in reviewed for p_ in parity)
    (OUT / 'number-parity-candidates.json').write_bytes(json_bytes(parity))

    # ---- structural parity
    struct = []
    for g, d in by_group.items():
        o = originals[g]
        en_user = d['en-tr']['messages'][1]['content']
        en_base = en_user[:len(en_user) - len(INSTRUCTION[('en', 'tr')])]
        for field, tr_text, en_text in [('user', o['user'], en_base), ('assistant', o['assistant'], d['tr-en']['messages'][2]['content']),
                                        ('reasoning', o['worked_solution'], d['tr-en']['worked_solution'])]:
            if tr_text is None:
                continue
            a, b = structure(tr_text), structure(en_text)
            if a != b:
                struct.append(dict(group=g, field=field, tr=a, en=b))
    reviewed_s = {(e['group'], e['field']) for e in exc['structural_parity']}
    for s_ in struct:
        if (s_['group'], s_['field']) not in reviewed_s:
            err(f'unreviewed structural parity mismatch {s_}')
    report['structural_parity_mismatches'] = len(struct)
    report['structural_parity_unreviewed'] = sum((s_['group'], s_['field']) not in reviewed_s for s_ in struct)
    (OUT / 'structural-parity-candidates.json').write_bytes(json_bytes(struct))

    # ---- constraint checks (both languages)
    def words(t):
        return len(re.findall(r"\w+(?:[’'-]\w+)*", t))

    cons = []

    def check(name, ok, detail):
        cons.append(dict(check=name, passed=bool(ok), detail=detail))
        if not ok:
            err(f'constraint {name}: {detail}')
    for lang, dirn in (('tr', 'tr-tr'), ('en', 'tr-en')):
        a = lambda g: by_group[f'bp01-{g}'][dirn]['messages'][2]['content']  # noqa: E731
        check(f'g103 50-80 words ({lang})', 50 <= words(a('g103')) <= 80, words(a('g103')))
        check(f'g115 <=120 words, no question mark ({lang})', words(a('g115')) <= 120 and '?' not in a('g115'), words(a('g115')))
        check(f'g121 <=150 words, exactly 3 bullets ({lang})', words(a('g121')) <= 150 and structure(a('g121'))['bullets'] == 3, [words(a('g121')), structure(a('g121'))['bullets']])
        check(f'g020 <=3 sentences ({lang})', len(re.findall(r'[.!?](?:\s|$)', a('g020'))) <= 3, len(re.findall(r'[.!?](?:\s|$)', a('g020'))))
        check(f'g001 exactly 3 bullets ({lang})', structure(a('g001'))['bullets'] == 3, structure(a('g001'))['bullets'])
        check(f'g100 starts with prefix, one paragraph ({lang})', a('g100').startswith('Kısaca:' if lang == 'tr' else 'In short:') and structure(a('g100'))['paragraphs'] == 1, a('g100')[:20])
        check(f'g048 single sentence ({lang})', len(re.findall(r'[.!?](?:\s|$)', a('g048'))) == 1, a('g048')[-30:])
        check(f'g043 number+unit only ({lang})', a('g043').strip() == ('55 dakika' if lang == 'tr' else '55 minutes'), a('g043'))
        check(f'g010 JSON valid ({lang})', isinstance(json.loads(a('g010')), list), 'json.loads ok')
    report['constraint_checks'] = cons

    # ---- independent arithmetic verification
    arith, arith_log = arith_checks(), []
    expected_values = {'g120': None}
    for g, (calc, must) in arith.items():
        grp = by_group[f'bp01-{g}']
        for dirn, lang in (('tr-tr', 'tr'), ('tr-en', 'en')):
            text = grp[dirn]['messages'][2]['content'] + '\n' + (grp[dirn]['worked_solution'] or '')
            have = set(number_multiset(text, lang))
            missing = [m for m in must if str(Decimal(m).normalize()) not in have]
            arith_log.append(dict(group=g, direction=dirn, computed={k: (str(v) if not isinstance(v, (int, float, str, tuple)) else v) for k, v in calc.items()},
                                  required_numbers=must, missing_in_answer=missing))
            if missing:
                err(f'{g} {dirn}: arithmetic values missing from answer/reasoning: {missing}')
    # explicit assertions against recomputation
    assert arith['g014'][0]['incl'] == 675 and arith['g021'][0]['total'] == 10400 and arith['g120'][0]['best'] == (1, 1, 2)
    assert arith['g153'][0]['implied_density'] != arith['g153'][0]['stated_density']
    report['arithmetic_groups_verified'] = len(arith)
    report['arithmetic_notes'] = ['g153 prompt is internally inconsistent (stated vs implied mean density); recorded as a translation-issue flag, not an error.']
    (OUT / 'arithmetic-verification.json').write_bytes(json_bytes(arith_log))

    # ---- heuristic language identification (insufficient alone; manual review is separate)
    lang_issues = []
    for r in train:
        for field, text in (('user', r['messages'][1]['content']), ('assistant', r['messages'][2]['content'])):
            lang = r['input_language'] if field == 'user' else r['output_language']
            tr_s, en_s = lang_score(text)
            if len(text.split()) >= 12 and ((lang == 'en' and tr_s > en_s) or (lang == 'tr' and en_s > tr_s)):
                lang_issues.append(dict(id=r['id'], field=field, expected=lang, tr_score=round(tr_s, 3), en_score=round(en_s, 3),
                                        effect=r['output_language_effect']))
    reviewed_l = {(e['id'], e['field']) for e in exc['language_heuristic']}
    for l_ in lang_issues:
        if (l_['id'], l_['field']) not in reviewed_l:
            err(f'unreviewed language heuristic flag {l_}')
    report['language_heuristic_flags'] = len(lang_issues)
    report['language_heuristic_unreviewed'] = sum((l_['id'], l_['field']) not in reviewed_l for l_ in lang_issues)
    (OUT / 'language-heuristic-flags.json').write_bytes(json_bytes(lang_issues))

    # ---- tokenizer statistics
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(str(TOKENIZER))
    assert tok.token_to_id('<|im_end|>') == 124900

    def render(r):
        m = r['messages']
        prefix = f"{BOS}<|im_start|>system\n{m[0]['content']}<|im_end|>\n<|im_start|>user\n{m[1]['content']}<|im_end|>\n<|im_start|>assistant\n"
        return prefix, prefix + '<think>' + (r['worked_solution'] or '') + '</think>' + m[2]['content'] + '<|im_end|>\n'
    audit = json.load(open(HISTORICAL_AUDIT, encoding='utf-8'))['rows']
    hist_ids = [json.loads(l)['input_ids'] for l in open(HISTORICAL_TOKENIZED, encoding='utf-8')]
    renderer_ok = 0
    for i, (src, a) in enumerate(zip(source_rows, audit)):
        m = src['messages']
        rr = dict(messages=m, worked_solution=src['worked_solution'])
        _, full = render(rr)
        ids = tok.encode(full, add_special_tokens=False).ids
        renderer_ok += int(full == a['rendered_text'] and ids == hist_ids[i])
    if renderer_ok != 160:
        err(f'renderer does not reproduce historical rendering/tokenization ({renderer_ok}/160)')
    rows_tok = []
    for r in train:
        prefix, full = render(r)
        ids = tok.encode(full, add_special_tokens=False).ids
        pl = len(tok.encode(prefix, add_special_tokens=False).ids)
        assert ids[:pl] == tok.encode(prefix, add_special_tokens=False).ids, 'token boundary changed'
        sup = len(ids) - pl
        if sup <= 0:
            err(f"{r['id']}: zero supervised tokens")
        if 124900 not in ids[pl:]:
            err(f"{r['id']}: missing end-of-turn in supervised span")
        if len(ids) > MAX_LENGTH:
            err(f"{r['id']}: length {len(ids)} > {MAX_LENGTH}")
        rows_tok.append(dict(id=r['id'], direction=r['direction'], category=r['category'], reasoning=r['has_reasoning'],
                             source_key=r['source_key'], length=len(ids), masked=pl, supervised=sup,
                             effect=r['output_language_effect']))
    groups = lambda key: collections.defaultdict(list)  # noqa: E731
    def stat_by(keyfn):
        acc = collections.defaultdict(lambda: collections.defaultdict(list))
        for t in rows_tok:
            for field in ('length', 'masked', 'supervised'):
                acc[keyfn(t)][field].append(t[field])
        return {str(k): {f: dist(v) for f, v in fields.items()} for k, fields in sorted(acc.items(), key=lambda kv: str(kv[0]))}
    token_report = dict(
        tokenizer=dict(path=TOKENIZER.relative_to(BASE.parents[2]).as_posix(), sha256=sha256_file(TOKENIZER),
                       note='local tokenizers library, no model weights; native LFM3 ChatML-like template rendered by a verified re-implementation',
                       renderer_verified_against_historical_pilot160=f'{renderer_ok}/160 rows byte-exact text and token IDs'),
        max_length=MAX_LENGTH, truncated_rows=sum(t['length'] > MAX_LENGTH for t in rows_tok),
        zero_supervised_rows=sum(t['supervised'] <= 0 for t in rows_tok),
        supervised_policy='assistant turn incl. <think>..</think>, end-of-turn id 124900 and trailing newline (matches pilot160 recipe)',
        overall=dict(length=dist([t['length'] for t in rows_tok]), masked=dist([t['masked'] for t in rows_tok]), supervised=dist([t['supervised'] for t in rows_tok])),
        by_direction=stat_by(lambda t: t['direction']), by_category=stat_by(lambda t: t['category']),
        by_reasoning=stat_by(lambda t: 'reasoning' if t['reasoning'] else 'direct_answer'),
        by_direction_and_reasoning=stat_by(lambda t: f"{t['direction']}|{'reasoning' if t['reasoning'] else 'direct'}"),
        by_source=stat_by(lambda t: t['source_key']),
        supervised_totals_by_direction={d: sum(t['supervised'] for t in rows_tok if t['direction'] == d) for d in DIRECTIONS},
        rows_per_direction=dict(per_dir))
    token_report['supervised_total_all'] = sum(token_report['supervised_totals_by_direction'].values())
    hist_total = 46088  # pilot160 preflight-local.json supervised_tokens
    if token_report['supervised_totals_by_direction']['tr-tr'] != hist_total:
        err(f"tr-tr supervised total {token_report['supervised_totals_by_direction']['tr-tr']} != historical {hist_total}")
    token_report['historical_pilot160_supervised_tokens'] = hist_total
    (OUT / 'token-length-report.json').write_bytes(json_bytes(token_report))
    (OUT / 'row-token-lengths.jsonl').write_bytes(''.join(json.dumps(t, ensure_ascii=False) + '\n' for t in rows_tok).encode('utf-8'))
    report['token_summary'] = dict(supervised_totals_by_direction=token_report['supervised_totals_by_direction'],
                                   supervised_total_all=token_report['supervised_total_all'],
                                   max_total_length=token_report['overall']['length']['max'], truncated_rows=token_report['truncated_rows'])

    report.update(status='passed' if not errors else 'FAILED', errors=errors, warnings=warnings,
                  generated_by='scripts/datasets/validate_lfm3_bilingual_pilot.py')
    (OUT / 'validation-report.json').write_bytes(json_bytes(report))
    print(report['status'], 'errors', len(errors), 'warnings', len(warnings))
    print(json.dumps({k: report[k] for k in ('counts', 'tr_tr_traceability', 'number_parity_mismatches', 'structural_parity_mismatches',
                                             'language_heuristic_flags', 'token_summary', 'en_output_language_effect')}, ensure_ascii=False, indent=1))
    for e in errors[:40]:
        print('ERROR', e)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
