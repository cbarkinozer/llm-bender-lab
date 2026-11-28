"""Build the exp-006 preference pairs from the parent's own samples, with code checks only (no model judge, no repair).

  python tr_dpo6_pairs.py build --prompts P.jsonl --answers A.jsonl [A2.jsonl ...] --out DIR \
      [--splits train] [--exclude-ids ids.json] [--min-rate 0.2] [--max-rate 0.8] [--ratio 0.8,1.25] [--max-per-prompt 2] \
      [--max-type-share 0.35] [--seed 3407]
  python tr_dpo6_pairs.py selftest

Per prompt: every sample is checked with tr_dpo6_checks.check_answer. A prompt is kept only when its pass rate lies in [min-rate, max-rate]
(prompts the parent always or never passes teach nothing). chosen = a passing sample, rejected = a failing sample of the same prompt, with
chosen/rejected word ratio inside --ratio, so DPO cannot win by shortening. At most --max-per-prompt pairs per prompt, never the same sample
twice. Pairs are then balanced by the type of the rejected answer's first failure: no type above --max-type-share of the pairs (possible only
with at least 1/share types; otherwise the cap is reported as unmet, never faked).
Output: pairs.jsonl (DPO rows), sft-control.jsonl (the same chosen answers, no rejected: the SFT control), pairs.manifest.json.
Prompt rows: id, prompt, check ({'items': [...]} or the legacy exp-004 spec), optional split / grounded / source.
Answer rows: the sampler format (id, sample, raw_output, finish_reason).
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'evaluation'))
import tr_dpo6_checks as C  # noqa: E402


def read_jsonl(path):
    with open(path, encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def visible(raw):
    return raw.replace('<|im_end|>', '').strip()


def items_from_check(check):
    """Items of a prompt: the new format, or the exp-004 legacy spec (max_words, exact_sentences, bullets, must_include)."""
    if not check:
        return None
    if 'items' in check:
        return check['items']
    items = []
    if 'max_words' in check:
        items.append(dict(type='max_words', n=check['max_words']))
    if 'exact_sentences' in check:
        items.append(dict(type='exact_sentences', n=check['exact_sentences']))
    if 'bullets' in check:
        items.append(dict(type='bullets', n=check['bullets']))
    items += [dict(type='must_include', word=w) for w in check.get('must_include', [])]
    return items or None


def failure_type(failures):
    first = failures[0]
    return re.split(r'[ >!<=]', first, 1)[0] if not first.startswith('not ended') else 'not_ended'


def n_words(text):
    return len(C.base.WORD.findall(text))


def candidates_for(prompt_row, samples):
    items = items_from_check(prompt_row.get('check'))
    out = []
    for s in samples:
        text = visible(s['raw_output'])
        res = C.check_answer(items, text, prompt_text=prompt_row['prompt'], ended=s['finish_reason'] == 'eos',
                             grounded=bool(prompt_row.get('grounded')))
        out.append(dict(sample=s['sample'], text=text, words=n_words(text), ok=res.ok, failures=res.failures))
    return out


def pick_pairs(cands, ratio, max_per_prompt):
    good = [c for c in cands if c['ok']]
    bad = [c for c in cands if not c['ok'] and c['words'] > 0 and c['text'].strip()]
    options = []
    for g in good:
        for b in bad:
            if g['text'] == b['text']:
                continue
            r = g['words'] / b['words'] if b['words'] else None
            if r is not None and ratio[0] <= r <= ratio[1]:
                options.append((abs(math.log(r)), g['sample'], b['sample'], g, b, r))
    options.sort(key=lambda o: (o[0], o[1], o[2]))
    used_g, used_b, picked = set(), set(), []
    for _, gi, bi, g, b, r in options:
        if gi in used_g or bi in used_b:
            continue
        used_g.add(gi)
        used_b.add(bi)
        picked.append((g, b, r))
        if len(picked) >= max_per_prompt:
            break
    return picked


def balance(pairs, share, seed):
    """Trim the largest failure-type groups until none exceeds `share` of the total (needs at least 1/share groups)."""
    rng = random.Random(seed)
    groups = {}
    for p in pairs:
        groups.setdefault(p['type'], []).append(p)
    met = len(groups) >= math.ceil(1 / share)
    while met:
        total = sum(len(v) for v in groups.values())
        biggest = max(groups, key=lambda k: len(groups[k]))
        if len(groups[biggest]) <= share * total + 1e-9:
            break
        groups[biggest].pop(rng.randrange(len(groups[biggest])))
    kept = [p for v in groups.values() for p in v]
    kept.sort(key=lambda p: p['pair_id'])
    return kept, met


def build(args):
    prompts = {r['id']: r for r in read_jsonl(args.prompts)}
    exclude = set(json.loads(args.exclude_ids.read_text(encoding='utf-8'))) if args.exclude_ids else set()
    answers = {}
    for path in args.answers:
        for a in read_jsonl(path):
            answers.setdefault(a['id'], []).append(a)
    ratio = tuple(float(x) for x in args.ratio.split(','))
    stats = dict(prompts=0, with_check=0, with_answers=0, kept_by_rate=0, always_pass=0, never_pass=0, no_pair=0)
    pairs = []
    for pid in sorted(prompts):
        row = prompts[pid]
        if pid in exclude or row.get('split', 'train') not in args.splits:
            continue
        stats['prompts'] += 1
        if not items_from_check(row.get('check')):
            continue
        stats['with_check'] += 1
        samples = sorted(answers.get(pid, []), key=lambda a: a['sample'])
        if not samples:
            continue
        stats['with_answers'] += 1
        cands = candidates_for(row, samples)
        rate = sum(c['ok'] for c in cands) / len(cands)
        if rate == 1.0:
            stats['always_pass'] += 1
        if rate == 0.0:
            stats['never_pass'] += 1
        if not (args.min_rate <= rate <= args.max_rate):
            continue
        stats['kept_by_rate'] += 1
        picked = pick_pairs(cands, ratio, args.max_per_prompt)
        if not picked:
            stats['no_pair'] += 1
        for k, (g, b, r) in enumerate(picked):
            pairs.append(dict(pair_id=f'{pid}#{k}', id=pid, source=row.get('source'), split=row.get('split', 'train'), prompt=row['prompt'],
                              chosen=g['text'], rejected=b['text'], chosen_sample=g['sample'], rejected_sample=b['sample'],
                              chosen_words=g['words'], rejected_words=b['words'], ratio=round(r, 4),
                              rejected_failures=b['failures'], type=failure_type(b['failures']), pass_rate=round(rate, 3)))
    before = len(pairs)
    pairs, share_met = balance(pairs, args.max_type_share, args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    write = lambda name, rows: (args.out / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8', newline='\n')  # noqa: E731
    write('pairs.jsonl', pairs)
    write('sft-control.jsonl', [dict(pair_id=p['pair_id'], id=p['id'], prompt=p['prompt'], chosen=p['chosen']) for p in pairs])
    n = max(1, len(pairs))
    manifest = dict(stats=stats, pairs_before_balance=before, pairs=len(pairs), type_share_cap=args.max_type_share, type_share_cap_met=share_met,
                    by_type={t: sum(p['type'] == t for p in pairs) for t in sorted({p['type'] for p in pairs})},
                    by_source={s: sum(p['source'] == s for p in pairs) for s in sorted({str(p['source']) for p in pairs})},
                    mean_words=dict(chosen=sum(p['chosen_words'] for p in pairs) / n, rejected=sum(p['rejected_words'] for p in pairs) / n),
                    mean_ratio=sum(p['ratio'] for p in pairs) / n,
                    params=dict(splits=args.splits, min_rate=args.min_rate, max_rate=args.max_rate, ratio=ratio,
                                max_per_prompt=args.max_per_prompt, seed=args.seed),
                    inputs=dict(prompts_sha256=hashlib.sha256(args.prompts.read_bytes()).hexdigest(),
                                answers_sha256=[hashlib.sha256(p.read_bytes()).hexdigest() for p in args.answers]),
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (args.out / 'pairs.manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(manifest, ensure_ascii=False, indent=1))
    return pairs, manifest


def selftest():
    import tempfile
    prompt = dict(id='x1', prompt='Konu hakkında yaz. En fazla 12 kelime kullan. Selamlama yazma.', split='train',
                  check=dict(items=[dict(type='max_words', n=12), dict(type='no_greeting')]))
    ok_text = 'Kısa bir metin burada yazılıdır ve sınır içindedir.'  # 9 words
    long_text = 'Bu metin sınırı aşar çünkü çok uzun bir cümle ile devam eder ve hiç bitmek bilmez gibi görünür.'  # 18 words
    greet = 'Merhaba, kısa bir metin burada yazılıdır ve kısa kalır.'  # 10 words, greeting
    tiny = 'Kısa.'
    samples = [ok_text, ok_text + ' Başka cümle yok.', long_text, greet, tiny, 'Başka bir doğru ve kısa metin cümlesi.']
    rows = [dict(id='x1', sample=i, raw_output=t + '<|im_end|>', finish_reason='eos') for i, t in enumerate(samples)]
    # y1: always passes, y2: never passes, y3: only a very different length fails (ratio out of range)
    p2 = dict(id='y1', prompt='Yaz. En fazla 50 kelime.', split='train', check=dict(items=[dict(type='max_words', n=50)]))
    p3 = dict(id='y2', prompt='Yaz. En fazla 2 kelime.', split='train', check=dict(items=[dict(type='max_words', n=2)]))
    p4 = dict(id='y3', prompt='Yaz. En fazla 12 kelime.', split='dev', check=dict(items=[dict(type='max_words', n=12)]))  # other split
    rows += [dict(id='y1', sample=i, raw_output=ok_text, finish_reason='eos') for i in range(4)]
    rows += [dict(id='y2', sample=i, raw_output=ok_text, finish_reason='eos') for i in range(4)]
    rows += [dict(id='y3', sample=i, raw_output=(ok_text if i % 2 else long_text), finish_reason='eos') for i in range(4)]
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / 'p.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in [prompt, p2, p3, p4]), encoding='utf-8')
        (d / 'a.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
        ns = argparse.Namespace(prompts=d / 'p.jsonl', answers=[d / 'a.jsonl'], out=d / 'o', splits=['train'], exclude_ids=None, min_rate=0.2,
                                max_rate=0.8, ratio='0.8,1.25', max_per_prompt=2, max_type_share=0.35, seed=1)
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            pairs, manifest = build(ns)
        ids = {p['id'] for p in pairs}
        assert ids == {'x1'}, ids  # y1 always passes, y2 never (its ok_text has 9 words > 2), y3 is another split
        assert 1 <= len(pairs) <= 2
        for p in pairs:
            assert 0.8 <= p['ratio'] <= 1.25
            assert C.check_answer(prompt['check']['items'], p['chosen']).ok
            assert not C.check_answer(prompt['check']['items'], p['rejected']).ok
            assert p['chosen'] != p['rejected'] and p['chosen_sample'] != p['rejected_sample']
        assert 'Kısa.' not in {p['rejected'] for p in pairs}  # 1 word: ratio far outside 0.8-1.25
        sft = read_jsonl(d / 'o' / 'sft-control.jsonl')
        assert [s['pair_id'] for s in sft] == [p['pair_id'] for p in pairs] and 'rejected' not in sft[0]
        assert manifest['type_share_cap_met'] is False  # one failure type only: the cap cannot be met and says so
        # legacy exp-004 check spec
        assert items_from_check(dict(max_words=40, bullets=3, must_include=['sabır'])) == [
            dict(type='max_words', n=40), dict(type='bullets', n=3), dict(type='must_include', word='sabır')]
        assert failure_type(['max_words 18>12']) == 'max_words' and failure_type(['not ended']) == 'not_ended'
        assert failure_type(['greeting']) == 'greeting'
    print('self-test ok')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['build', 'selftest'])
    ap.add_argument('--prompts', type=Path)
    ap.add_argument('--answers', type=Path, nargs='+')
    ap.add_argument('--out', type=Path)
    ap.add_argument('--splits', nargs='+', default=['train'])
    ap.add_argument('--exclude-ids', type=Path)
    ap.add_argument('--min-rate', type=float, default=0.2)
    ap.add_argument('--max-rate', type=float, default=0.8)
    ap.add_argument('--ratio', default='0.8,1.25')
    ap.add_argument('--max-per-prompt', type=int, default=2)
    ap.add_argument('--max-type-share', type=float, default=0.35)
    ap.add_argument('--seed', type=int, default=3407)
    args = ap.parse_args()
    if args.command == 'selftest':
        selftest()
    else:
        assert args.prompts and args.answers and args.out, '--prompts, --answers and --out are required'
        build(args)


if __name__ == '__main__':
    main()
