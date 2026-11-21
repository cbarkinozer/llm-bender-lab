"""Build LFM3 eval v2 packets (evaluation only, never training data).

Families built here: paired EN/TR GSM8K test items and symbolic arithmetic.
Sources are pinned by revision and sha256; selection is deterministic.
Packets go to eval-v2/data-local (ignored by Git: the Turkish GSM8K card has no license);
manifest-core.json with ids, hashes and audit counts is committed.
Existing packets must match byte for byte, otherwise the script refuses to run.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from typing import NamedTuple
import random
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'evaluation'))
import lfm3_eval_v2_scoring as scoring  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / 'experiments/turkish-capability/lfm3-1.7b/eval-v2'


class Source(NamedTuple):
    repo: str
    revision: str
    file: str
    rows: int
    license: str
    sha256: str


SOURCES = {
    'en': Source('openai/gsm8k', '740312add88f781978c0658806c59bc2815b9866', 'main/test-00000-of-00001.parquet',
                 1319, 'mit', 'ee7b8da9e381df27b9e3f7758a159ab2bdaa4dbaa910546cbbc47e0cb44e4f59'),
    'tr': Source('malhajar/gsm8k_tr-v0.2', 'f05ded624e64f2e9b2c384c91ed13e46922c70a1', 'data/test-00000-of-00001.parquet',
                 1317, 'none declared', 'c0534fc59e35e5df05e6a2829ff9da151097b5174dce6b5196468d5980d3d8bd'),
}
SEED = 'eval-v2-20261121'
MATH_PER_BUCKET = {1: 38, 2: 38, 3: 38, 4: 38}  # solution-step buckets: <=2, 3, 4, >=5
PROMPTS = dict(
    math_en='{q}\n\nSolve it step by step. End your reply with a line of the form "Final answer: <number>".',
    math_tr='{q}\n\nAdım adım çöz. Yanıtını "Nihai cevap: <sayı>" biçiminde bir satırla bitir.',
    symbolic_en='{e} = ?\nOutput only the number.',
    symbolic_tr='{e} = ?\nYalnızca sayıyı yaz.',
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def rank(key):
    return sha256(f'{SEED}:{key}'.encode())


def load_source(lang, cache):
    import pyarrow.parquet as pq
    spec = SOURCES[lang]
    path = cache / spec.repo.replace('/', '__') / spec.file
    if not path.exists():
        from huggingface_hub import hf_hub_download
        hf_hub_download(spec.repo, spec.file, repo_type='dataset', revision=spec.revision,
                        local_dir=str(cache / spec.repo.replace('/', '__')))
    if sha256(path.read_bytes()) != spec.sha256:
        raise ValueError(f'Pinned source checksum mismatch: {spec.repo}')
    rows = pq.read_table(path).to_pylist()
    if len(rows) != spec.rows:
        raise ValueError(f'Unexpected row count for {spec.repo}')
    return rows


def norm_num(token):
    token = token.replace(',', '')
    if re.fullmatch(r'\d{1,3}(\.\d{3})+', token):
        token = token.replace('.', '')
    if '.' in token:
        token = token.rstrip('0').rstrip('.')
    return token


def numbers(text):
    return Counter(norm_num(t) for t in re.findall(r'\d[\d.,]*\d|\d', text))


def final_answer(answer):
    match = re.search(r'####\s*([-\d.,]+)', answer)
    return norm_num(match.group(1)) if match else None


def align(en, tr):
    """Pair EN and TR GSM8K items; keep a pair only when all invariants hold."""
    en_final = [final_answer(r['answer']) for r in en]
    tr_final = [final_answer(r['answer']) for r in tr]
    pairs, drops, used, cursor = [], Counter(), set(), 0
    dropped = []
    for i, row in enumerate(en):
        best = None
        for j in range(max(0, cursor - 5), min(len(tr), cursor + 12)):
            if j in used or not (0 <= i - j <= 2) or en_final[i] != tr_final[j] or en_final[i] is None:
                continue
            en_n, tr_n = numbers(row['question']), numbers(tr[j]['question'])
            overlap = sum((en_n & tr_n).values()) / max(1, sum(en_n.values()))
            extra = sum((tr_n - en_n).values())
            if best is None or overlap > best[1]:
                best = (j, overlap, extra)
        if best is None:
            drops['no_tr_item_with_same_final_answer'] += 1
            dropped.append(i)
        elif best[1] < 0.999:
            drops['question_numbers_not_preserved'] += 1
            dropped.append(i)
        elif best[2]:
            drops['extra_numbers_in_tr_question'] += 1
            dropped.append(i)
        else:
            used.add(best[0])
            pairs.append((i, best[0]))
            cursor = best[0] + 1
    return pairs, dict(drops), dropped


def build_math(cache):
    en, tr = load_source('en', cache), load_source('tr', cache)
    pairs, drops, dropped = align(en, tr)
    # solution steps (calculator annotations): <=2 -> bucket 1, 3 -> 2, 4 -> 3, >=5 -> 4
    buckets = {1: [], 2: [], 3: [], 4: []}
    for i, j in pairs:
        steps = en[i]['answer'].count('<<')
        buckets[1 if steps <= 2 else 2 if steps == 3 else 3 if steps == 4 else 4].append((i, j))
    chosen = []
    for bucket, quota in MATH_PER_BUCKET.items():
        ranked = sorted(buckets[bucket], key=lambda p: rank(f'gsm8k:{p[0]}'))
        if len(ranked) < quota:
            raise ValueError(f'Bucket {bucket} has only {len(ranked)} clean pairs')
        chosen.extend((bucket, p) for p in ranked[:quota])
    chosen.sort(key=lambda c: rank(f'order:{c[1][0]}'))
    rows, meta = [], []
    for n, (bucket, (i, j)) in enumerate(chosen, 1):
        pair_id = f'ev2-math-{n:03d}'
        gold = final_answer(en[i]['answer'])
        for lang, source, index in (('en', en, i), ('tr', tr, j)):
            question = ' '.join(source[index]['question'].split())
            rows.append(dict(id=f'{pair_id}-{lang}', pair_id=pair_id, family='math', language=lang,
                             messages=[dict(role='user', content=PROMPTS[f'math_{lang}'].format(q=question))],
                             gold=gold, step_bucket=bucket, source_index=index,
                             evaluation_only=True, training_allowed=False))
        meta.append(dict(pair_id=pair_id, en_index=i, tr_index=j, step_bucket=bucket, gold=gold))
        # sanity: the scorer must accept the gold answer rewritten in the requested format
        for lang, marker in (('en', 'Final answer'), ('tr', 'Nihai cevap')):
            value, method = scoring.extract_final_number(f'... {marker}: {gold}', lang)
            assert method == 'marker' and str(value) == gold, (pair_id, lang, value, method)
    audit = dict(en_rows=len(en), tr_rows=len(tr), clean_pairs=len(pairs), dropped_en_items=len(dropped),
                 drop_reasons=drops, clean_pairs_by_bucket={str(k): len(v) for k, v in buckets.items()},
                 selected=len(meta), selection=f'sha256("{SEED}:gsm8k:<en_index>") rank within step bucket')
    return rows, meta, audit


def exact_eval(text):
    """Evaluate +,-,*,/ and parentheses over integers with exact fractions; nothing else is allowed."""
    import ast
    import operator
    table = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}

    def walk(n):
        if isinstance(n, ast.Expression):
            return walk(n.body)
        if isinstance(n, ast.BinOp) and type(n.op) in table:
            return table[type(n.op)](walk(n.left), walk(n.right))
        if isinstance(n, ast.Constant) and type(n.value) is int:
            return Fraction(n.value)
        raise ValueError(f'Unsupported expression element: {ast.dump(n)}')
    return walk(ast.parse(text, mode='eval'))


def build_symbolic(count_per_ops=20, op_counts=(2, 3, 4)):
    rng = random.Random(20261121)
    seen, items = set(), []

    def node(ops_left):
        if ops_left == 0:
            value = rng.randint(2, 99)
            return str(value), Fraction(value), 9
        left_ops = rng.randint(0, ops_left - 1)
        ls, lv, lp = node(left_ops)
        rs, rv, rp = node(ops_left - 1 - left_ops)
        op = rng.choice('+-*/')
        prec = 1 if op in '+-' else 2
        if op == '/' and (rv == 0 or (lv / rv).denominator != 1):
            raise ArithmeticError
        value = {'+': lv + rv, '-': lv - rv, '*': lv * rv, '/': lv / rv if rv else 0}[op]
        if lp < prec:
            ls = f'({ls})'
        if rp <= prec:  # leaves have precedence 9; any binary right child is parenthesized
            rs = f'({rs})'
        return f'{ls} {op} {rs}', value, prec

    for ops in op_counts:
        made = 0
        while made < count_per_ops:
            try:
                text, value, _ = node(ops)
            except ArithmeticError:
                continue
            if value.denominator != 1 or not (0 <= value < 100000) or text in seen:
                continue
            seen.add(text)
            items.append((ops, text, int(value)))
            made += 1
    rng.shuffle(items)
    rows, meta = [], []
    for n, (ops, text, value) in enumerate(items, 1):
        pair_id = f'ev2-sym-{n:03d}'
        assert exact_eval(text) == value, (text, value)  # independent AST evaluation, exact fractions
        for lang in ('en', 'tr'):
            rows.append(dict(id=f'{pair_id}-{lang}', pair_id=pair_id, family='symbolic', language=lang,
                             messages=[dict(role='user', content=PROMPTS[f'symbolic_{lang}'].format(e=text))],
                             gold=str(value), operators=ops, evaluation_only=True, training_allowed=False))
        meta.append(dict(pair_id=pair_id, expression=text, gold=str(value), operators=ops))
    return rows, meta, dict(count=len(meta), by_operators=dict(Counter(m['operators'] for m in meta)))


BFCL_REPO = 'gorilla-llm/Berkeley-Function-Calling-Leaderboard'
BFCL_REVISION = '61fc0608cfd831fcfbbaa676ebdfef0ed963eeda'
BFCL_FILES = {
    'BFCL_v3_simple.json': 'fbc37b2ad252bf9af985582e0e07b456173fe627d957491472ea9cef5fb83158',
    'possible_answer/BFCL_v3_simple.json': '2911a2bc00df82c4f999ffa64fedb0164cb88e96212ffa5972087eb91fd496ee',
    'BFCL_v3_multiple.json': 'aef168155ebd74b7ac2401198b201343bc7d16d7a3d7e0d4e6d8ee82c6969b2a',
    'possible_answer/BFCL_v3_multiple.json': '244e00ce9395df948bcafc7bee64e8f9c87ef70887587d83cae45b13699f3047',
    'BFCL_v3_parallel.json': 'fad375d68295776efb63e5aa331dd884f8635e7bb50e05908113c74f14281c3c',
    'possible_answer/BFCL_v3_parallel.json': '3af54bf04e5b7640b03a9b6a82440f52474feb24b398f94435fd2b155c7727de',
}
BFCL_QUOTA = {'simple': 40, 'multiple': 20, 'parallel': 20}
TYPE_MAP = {'dict': 'object', 'float': 'number', 'tuple': 'array'}
# Generic words that are translated on purpose (the model must map them to English schema values).
# Phrases whose entity or numbers are kept (checked separately) while the generic words are translated.
ENTITY_EXEMPT = {'December', 'Euros', 'Chicago area', '24 hour', 'Canadian dollars', 'May 12, 2022'}


def load_bfcl(cache, name):
    path = cache / BFCL_REPO.replace('/', '__') / name
    if not path.exists():
        from huggingface_hub import hf_hub_download
        hf_hub_download(BFCL_REPO, name, repo_type='dataset', revision=BFCL_REVISION,
                        local_dir=str(cache / BFCL_REPO.replace('/', '__')))
    if sha256(path.read_bytes()) != BFCL_FILES[name]:
        raise ValueError(f'Pinned source checksum mismatch: {name}')
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def convert_types(node):
    """BFCL pseudo types -> JSON-schema types, recursively."""
    if isinstance(node, dict):
        return {k: (TYPE_MAP.get(v, v) if k == 'type' and isinstance(v, str) else convert_types(v))
                for k, v in node.items()}
    if isinstance(node, list):
        return [convert_types(v) for v in node]
    return node


def first_value(alternatives):
    """Pick a gold-accepted value for oracle outputs (first non-empty alternative)."""
    def resolve(alt):
        if isinstance(alt, dict):  # dict values are lists of alternatives per key
            return {k: first_value(v) for k, v in alt.items()}
        if isinstance(alt, list):
            return [resolve(x) for x in alt]
        return alt
    return resolve(next(a for a in alternatives if a != ''))


def number_set(text, lang):
    values = set()
    for token in re.findall(r'\d[\d.,]*\d|\d', text):
        parsed = scoring.parse_number(token, lang)
        values.add(parsed if parsed is None else parsed.normalize())
    return values


def check_translation(pair_id, en, tr, gold_calls):
    """Return a list of invariant violations between the English and Turkish query."""
    problems = []
    if number_set(en, 'en') != number_set(tr, 'tr'):
        problems.append(f'numbers differ: {sorted(map(str, number_set(en, "en")))} vs {sorted(map(str, number_set(tr, "tr")))}')
    for ident in re.findall(r"\b[a-z]+(?:_[a-z]+)+(?:\.[a-z_]+)?\b", en):
        if ident not in tr:
            problems.append(f'identifier missing: {ident}')
    literals = set()

    def collect(value):
        if isinstance(value, str):
            literals.add(value)
        elif isinstance(value, list):
            for v in value:
                collect(v)
        elif isinstance(value, dict):
            for v in value.values():
                collect(v)
    for call in gold_calls:
        collect(list(next(iter(call.values())).values()))
    for literal in literals:
        needs_check = literal and literal in en and literal not in ENTITY_EXEMPT and (
            any(c.isupper() or c.isdigit() or not c.isalnum() and c != ' ' for c in literal))
        if needs_check and literal not in tr:
            problems.append(f'gold literal not preserved: {literal!r}')
    return problems


def build_toolcall(cache):
    translations = json.loads((EXP / 'toolcall-translations-tr.json').read_text(encoding='utf-8'))
    translations.pop('_policy')
    chosen = []
    for family, quota in BFCL_QUOTA.items():
        questions = load_bfcl(cache, f'BFCL_v3_{family}.json')
        answers = {r['id']: r['ground_truth'] for r in load_bfcl(cache, f'possible_answer/BFCL_v3_{family}.json')}
        ranked = sorted(questions, key=lambda r: rank(f'bfcl:{r["id"]}'))[:quota]
        chosen.extend((family, r, answers[r['id']]) for r in ranked)
    if set(translations) != {r['id'] for _, r, _ in chosen}:
        raise ValueError('Translation ids do not match the selected BFCL items: '
                         f'{sorted(set(translations) ^ {r["id"] for _, r, _ in chosen})}')
    chosen.sort(key=lambda c: rank(f'order:{c[1]["id"]}'))
    rows, meta, violations = [], [], {}
    for n, (family, record, gold) in enumerate(chosen, 1):
        pair_id = f'ev2-tool-{n:03d}'
        en = record['question'][0][0]['content'].strip()
        if len(en) > 1 and en[0] == en[-1] == '"':
            en = en[1:-1].strip()
        en = ' '.join(en.split())
        tr = translations[record['id']]
        problems = check_translation(pair_id, en, tr, gold)
        if problems:
            violations[record['id']] = problems
        tools = convert_types(record['function'])
        for lang, query in (('en', en), ('tr', tr)):
            rows.append(dict(id=f'{pair_id}-{lang}', pair_id=pair_id, family='toolcall', subfamily=family,
                             language=lang, messages=[dict(role='user', content=query)], tools=tools,
                             gold_calls=gold, bfcl_id=record['id'], evaluation_only=True, training_allowed=False))
        meta.append(dict(pair_id=pair_id, bfcl_id=record['id'], subfamily=family, n_gold_calls=len(gold)))
        # oracle: gold-derived output passes; mutated outputs fail
        calls = [(name, {k: first_value(v) for k, v in params.items() if '' not in v or v[0] != ''})
                 for entry in gold for name, params in entry.items()]
        oracle = '</think>' + ''.join(scoring.render_call_xml(name, args) for name, args in calls)
        result = scoring.score_toolcall(oracle, gold, tools, True)
        assert result['correct'], (pair_id, record['id'], result)
        wrong_name = oracle.replace(f'<function={calls[0][0]}>', '<function=nonexistent_fn>')
        assert not scoring.score_toolcall(wrong_name, gold, tools, True)['correct'], pair_id
        if calls[0][1]:
            first_key = next(iter(calls[0][1]))
            mutated = oracle.replace(f'<parameter={first_key}>', f'<parameter={first_key}_x>', 1)
            assert not scoring.score_toolcall(mutated, gold, tools, True)['correct'], pair_id
        assert not scoring.score_toolcall('</think>Sure, here is the answer.', gold, tools, True)['correct']
    if violations:
        raise ValueError('Turkish translation invariants failed:\n' + json.dumps(violations, indent=1, ensure_ascii=False))
    types = Counter(p.get('type') for r in rows if r['language'] == 'en' for t in r['tools']
                    for p in t['parameters']['properties'].values())
    audit = dict(count=len(meta), by_subfamily=dict(Counter(m['subfamily'] for m in meta)),
                 schema_types=dict(types), entity_exempt=sorted(ENTITY_EXEMPT),
                 translation_author='Claude Sonnet 5.5, 2026-11-21, owner spot check pending',
                 invariants='number sets equal; identifiers kept; gold literals with uppercase/digits/symbols kept verbatim')
    return rows, meta, audit


def write_frozen(path, rows):
    blob = ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in rows).encode('utf-8')
    if path.exists() and path.read_bytes() != blob:
        raise ValueError(f'Refusing to change frozen packet {path.name}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)
    return dict(file=path.name, rows=len(rows), sha256=sha256(blob))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, default=EXP / 'data-local/source-cache')
    args = parser.parse_args()
    math_rows, math_meta, math_audit = build_math(args.cache)
    sym_rows, sym_meta, sym_audit = build_symbolic()
    tool_rows, tool_meta, tool_audit = build_toolcall(args.cache)
    local = EXP / 'data-local'
    packets = [write_frozen(local / 'math-pairs.jsonl', math_rows),
               write_frozen(local / 'symbolic-pairs.jsonl', sym_rows),
               write_frozen(local / 'toolcall-pairs.jsonl', tool_rows)]
    manifest = dict(
        version='eval-v2 core draft 1 (math, symbolic); more families are added before freeze',
        frozen=False, seed=SEED, scorer=scoring.SCORER_VERSION,
        builder_sha256=sha256(Path(__file__).read_bytes()),
        scorer_sha256=sha256((ROOT / 'scripts/evaluation/lfm3_eval_v2_scoring.py').read_bytes()),
        sources={k: v._asdict() for k, v in SOURCES.items()}, prompts=PROMPTS, packets=packets,
        bfcl=dict(repo=BFCL_REPO, revision=BFCL_REVISION, license='apache-2.0', files=BFCL_FILES),
        math=dict(audit=math_audit, pairs=math_meta), symbolic=dict(audit=sym_audit, items=sym_meta),
        toolcall=dict(audit=tool_audit, items=tool_meta),
        policy='Evaluation only. Gold answers come from English GSM8K; Turkish items are kept only when the final '
               'answer and every question number match. Not a Turkish-quality benchmark: translation is machine-made.')
    out = EXP / 'manifest-core.json'
    blob = json.dumps(manifest, indent=1, ensure_ascii=False) + '\n'
    if out.exists():
        previous = json.loads(out.read_text(encoding='utf-8'))
        if previous.get('frozen') and previous != json.loads(blob):
            raise ValueError('manifest-core.json is frozen; create a new eval version instead')
        if any(p not in manifest['packets'] for p in previous['packets']):
            raise ValueError('An existing packet changed after the manifest was written; investigate before overwriting')
    out.write_text(blob, encoding='utf-8')
    print(json.dumps(dict(math=math_audit, symbolic=sym_audit, packets=packets), indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
