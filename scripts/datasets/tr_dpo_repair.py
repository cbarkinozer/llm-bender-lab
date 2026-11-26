"""Repaired-answer DPO data for Turkish (preference-rl exp-005): a strong model fixes the SFT model's own answers, we validate and pair them.

  python tr_dpo_repair.py pool     --prompts P --answers A --out-data DIR --out-local DIR [--train 2000] [--heldout 200] [--pilot 300]
                                   [--drop-plain-after-pilot]
  python tr_dpo_repair.py validate --packet PACKET --results R1 [R2 ...] --accept WORDS --out DIR
  python tr_dpo_repair.py pairs    --validated DIR/validated.jsonl --out FILE

pool      Only prompts that carry their own data (Atlas constraint prompts, context prompts, plain prompts with a source block). One
          finished sample of exp-021 per prompt is the answer to repair. A held-out set is cut first and never enters the packets.
validate  The repair model answers each packet row with verdict none | minimal | larger | rewrite_needed, the complete repaired answer
          and a list of changes. A repair is usable when the detectors and the constraint checker pass, the word count stays in
          [0.50, 1.10] of the original (or within 5 words for short answers) and it ends like a finished answer. Later result files
          override earlier ones for the same id (retry). `rewrite_needed` and failed retries are dropped.
pairs     rejected = the SFT model's own answer, chosen = the repaired answer, labelled `synthetic_repair`.
"""
import argparse
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tr_dpo_flags as F  # noqa: E402
from tr_dpo_flags import read_jsonl, write_jsonl, visible, words  # noqa: E402

SEED = 'exp005'
BAND = (0.50, 1.10)  # pilot: 0.70 turned fixable answers into rewrites (removing invented content shortens an answer); mean ratio is guarded in `pairs`
MIN_MEAN_RATIO = 0.85
BOUND_CITED = re.compile(r'alt s[ıi]n[ıi]r|asgari uzunluk|kelime(lik)?\s+(alt\s+)?(s[ıi]n[ıi]r|aral)|aralık|dolgu|word range|lower bound|padding', re.I)
SHORT_WORDS = 20
VERDICTS = ('none', 'minimal', 'larger', 'rewrite_needed')
MIN_ANSWER_WORDS = 8
SOURCE_WORDS = 15  # a plain prompt carries data when this many words follow its first line break


def rank(*parts):
    return hashlib.sha256(('|'.join((SEED,) + tuple(str(p) for p in parts))).encode('utf-8')).hexdigest()


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def group_of(row):
    """constraint / context / plain_source for prompts that carry data; None for open questions and templates."""
    if row['kind'] == 'atlas_constraint':
        return 'constraint'
    if row['kind'] == 'atlas_context':
        return 'context'
    if row['kind'] == 'atlas_plain':
        tail = row['prompt'].split('\n', 1)[1] if '\n' in row['prompt'] else ''
        return 'plain_source' if len(tail.split()) >= SOURCE_WORDS else None
    return None


def repair_input(p):
    """What the repair model sees: the prompt, the answer to repair, the limits checked by code and the word range to stay in."""
    w = p['answer_words']
    low, high = (w - 5, w + 5) if w < SHORT_WORDS else (-(-w * round(BAND[0] * 100) // 100), w * round(BAND[1] * 100) // 100)
    return dict(id=p['id'], prompt=p['prompt'], answer=p['answer'], limits_checked_by_code=p['check'], answer_words=w, repaired_word_range=[max(1, low), high])


def cmd_pool(args):
    prompts = read_jsonl(args.prompts)
    answers = read_jsonl(args.answers)
    by_prompt = {}
    for a in answers:
        text = visible(a['raw_output'])
        if a['finish_reason'] == 'eos' and not a.get('hit_max_new_tokens') and len(words(text)) >= MIN_ANSWER_WORDS:
            by_prompt.setdefault(a['id'], []).append(a)
    groups = {}
    for row in prompts:
        g = group_of(row)
        if g and row['id'] in by_prompt:
            groups.setdefault(g, []).append(row)
    for g in groups:
        groups[g].sort(key=lambda r: rank('split', r['id']))
    sizes = {g: len(v) for g, v in groups.items()}
    total = sum(sizes.values())
    assert total >= args.train + args.heldout, f'only {total} eligible prompts: {sizes}'
    heldout_quota = {g: round(args.heldout * n / total) for g, n in sizes.items()}
    heldout_quota['constraint'] += args.heldout - sum(heldout_quota.values())
    heldout = {g: groups[g][:heldout_quota[g]] for g in groups}
    rest = {g: groups[g][heldout_quota[g]:] for g in groups}
    # train: all context prompts, constraint prompts up to 65%, the rest plain-with-source (as many as exist)
    train_quota = dict(context=len(rest.get('context', [])), constraint=min(len(rest['constraint']), int(args.train * 0.65)))
    train_quota['plain_source'] = min(len(rest.get('plain_source', [])), args.train - sum(train_quota.values()))
    short = args.train - sum(train_quota.values())
    train_quota['constraint'] = min(len(rest['constraint']), train_quota['constraint'] + short)
    train = []
    for g, n in train_quota.items():
        for row in rest.get(g, [])[:n]:
            train.append((g, row))
    train.sort(key=lambda t: rank('order', t[1]['id']))
    def entry(g, row):
        ranked = sorted(by_prompt[row['id']], key=lambda a: rank('sample', row['id'], a['sample']))
        a = ranked[0]
        alt = ranked[1]['sample'] if len(ranked) > 1 else None
        text = visible(a['raw_output'])
        return dict(id=row['id'], kind=row['kind'], group=g, prompt=row['prompt'], check=row['check'], sample=a['sample'], alt_sample=alt,
                    answer=text, answer_words=len(words(text)))

    packet = [entry(g, row) for g, row in train]
    pilot, rest_packet = packet[:args.pilot], packet[args.pilot:]
    if args.drop_plain_after_pilot:
        # pilot yield: plain_source 22% usable, constraint 64%; refill the rest with the unused constraint prompts (the pilot stays as it was)
        unused = rest['constraint'][train_quota['constraint']:]
        dropped = [p for p in rest_packet if p['group'] == 'plain_source']
        assert len(unused) >= len(dropped), f'only {len(unused)} unused constraint prompts for {len(dropped)} dropped plain_source prompts'
        kept = [p for p in rest_packet if p['group'] != 'plain_source']
        rest_packet = sorted(kept + [entry('constraint', r) for r in unused[:len(dropped)]], key=lambda p: rank('order', p['id']))
        packet = pilot + rest_packet
    args.out_local.mkdir(parents=True, exist_ok=True)
    args.out_data.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_local / 'repair-packet-pilot.jsonl', pilot)
    write_jsonl(args.out_local / 'repair-packet-rest.jsonl', rest_packet)
    for name, part in (('pilot', pilot), ('rest', rest_packet)):
        write_jsonl(args.out_local / f'repair-input-{name}.jsonl', [repair_input(p) for p in part])
    held_rows = [dict(id=r['id'], kind=r['kind'], group=g, prompt=r['prompt'], check=r['check']) for g, rs in heldout.items() for r in rs]
    write_jsonl(args.out_local / 'heldout-prompts.jsonl', held_rows)
    manifest = dict(seed=SEED, eligible_by_group=sizes, heldout_quota=heldout_quota, train_quota=train_quota, train_prompts=len(packet),
                    pilot=len(pilot), heldout=len(held_rows), heldout_ids=sorted(r['id'] for r in held_rows),
                    train_ids=[p['id'] for p in packet], pilot_ids=[p['id'] for p in pilot],
                    samples={p['id']: [p['sample'], p['alt_sample']] for p in packet},
                    inputs=dict(prompts_sha256=sha256_file(args.prompts), answers_sha256=sha256_file(args.answers)),
                    train_by_group=dict(Counter(p['group'] for p in packet)), rest_by_group=dict(Counter(p['group'] for p in rest_packet)),
                    rules=dict(band=BAND, short_words=SHORT_WORDS, min_answer_words=MIN_ANSWER_WORDS, source_words=SOURCE_WORDS,
                               drop_plain_after_pilot=args.drop_plain_after_pilot))
    (args.out_data / 'repair-pool-manifest.json').write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: manifest[k] for k in ('eligible_by_group', 'heldout_quota', 'train_quota', 'train_by_group', 'rest_by_group', 'train_prompts', 'pilot', 'heldout')}, indent=1))
    print('packet words (median):', sorted(p['answer_words'] for p in packet)[len(packet) // 2])


def normalized(text):
    """Detector false alarms seen in the audit: decimal numbers cut sentences, 'N-' / 'N)' were not read as list markers."""
    text = re.sub(r'(\d)[.,](\d)', r'\1\2', text)
    return re.sub(r'(?m)^\s*\d+\s*[.)\-]\s+', '- ', text)


def check_repair(analyzer, row, result, accept):
    """Reasons a repair is not usable (empty list: usable), plus measurements."""
    verdict = result.get('verdict')
    if verdict not in VERDICTS:
        return ['verdict must be one of ' + ', '.join(VERDICTS)], {}
    if verdict in ('none', 'rewrite_needed'):
        return [f'verdict {verdict}'], {}
    chosen = (result.get('chosen') or '').strip()
    if not chosen:
        return ['empty chosen'], {}
    if not result.get('changes'):
        return ['no list of changes'], {}
    original = row['answer'].strip()
    if chosen == original:
        return ['identical to the original answer'], {}
    wa, wb = len(words(original)), len(words(chosen))
    ratio = wb / max(1, wa)
    m = dict(words_before=wa, words_after=wb, length_ratio=round(ratio, 3),
             word_edit_ratio=round(1 - difflib.SequenceMatcher(None, words(original), words(chosen), autojunk=False).ratio(), 3),
             char_similarity=round(difflib.SequenceMatcher(None, original, chosen, autojunk=False).ratio(), 3))
    problems = []
    if wa >= SHORT_WORDS:
        if not BAND[0] <= ratio <= BAND[1]:
            problems.append(f'length ratio {ratio:.2f} outside {BAND}')
    elif abs(wb - wa) > 5:
        problems.append('short answer changed by more than 5 words')
    prompt_row = dict(kind=row['kind'], prompt=row['prompt'], check=row['check'])
    f = F.flags_for(analyzer, prompt_row, chosen, True, accept=accept)
    if f['constraint']:
        again = F.flags_for(analyzer, prompt_row, normalized(chosen), True, accept=accept)['constraint']
        if again:
            problems += [f'constraint fails: {c}' for c in f['constraint']]
        else:
            m['constraint_normalized'] = True
    for key in ('empty', 'english_reply', 'loop'):
        if f[key]:
            problems.append(f'flagged: {key}')
    if f['unknown_words']:
        problems.append('unknown words: ' + ', '.join(f['unknown_words']))
    if f['english_words']:
        problems.append('English words: ' + ', '.join(f['english_words']))
    structured = bool(re.search(r'^\s*\|?\s*:?-{3,}:?\s*\|', chosen, re.M) and chosen.endswith('|')) or \
        (chosen.startswith('```') and chosen.endswith('```') and chosen.count('```') % 2 == 0)
    last_line = chosen.rstrip().splitlines()[-1]
    list_item = bool(re.match(r'\s*(?:[-*•]|\d+\s*[.)\-])\s+\S', last_line))  # a list item needs no final period
    if not structured and not list_item and chosen[-1] not in '.!?…"\')”»)]}*':
        problems.append('does not end like a finished answer')
    return problems, m


def cmd_validate(args):
    packet = {r['id']: r for r in read_jsonl(args.packet)}
    latest = {}
    for i, path in enumerate(args.results):
        for r in read_jsonl(path):
            assert r['id'] in packet, f"result for an id that is not in the packet: {r['id']}"
            latest[r['id']] = (i, r)
    accept = {w.strip() for w in Path(args.accept).read_text(encoding='utf-8').splitlines() if w.strip() and not w.startswith('#')}
    analyzer = F.nonword.Analyzer()
    report, usable_rows = [], []
    for pid, (i, result) in latest.items():
        problems, m = check_repair(analyzer, packet[pid], result, accept)
        ok = not problems
        report.append(dict(id=pid, usable=ok, verdict=result.get('verdict'), attempt=i + 1, problems=problems, group=packet[pid]['group'], **m))
        if ok:
            usable_rows.append(dict(id=pid, kind=packet[pid]['kind'], group=packet[pid]['group'], prompt=packet[pid]['prompt'],
                                    check=packet[pid]['check'], rejected=packet[pid]['answer'].strip(), chosen=result['chosen'].strip(),
                                    verdict=result['verdict'], changes=result['changes'], **m))
    answered = set(latest)
    retry = []
    if len(args.results) == 1:
        for r in report:
            res = latest[r['id']][1]
            if not r['usable'] and r['verdict'] in ('minimal', 'larger'):
                retry.append(repair_input(packet[r['id']]) | dict(retry='check_failed', failure_reasons=r['problems'], previous_chosen=res['chosen']))
            elif r['verdict'] == 'rewrite_needed' and BOUND_CITED.search(' '.join(res.get('changes') or [])):
                retry.append(repair_input(packet[r['id']]) | dict(retry='range_widened', previous_reason=res.get('changes')))
    missing = [pid for pid in packet if pid not in answered]
    verdicts = Counter(r['verdict'] for r in report)
    summary = dict(packet=len(packet), answered=len(answered), missing=len(missing), verdicts=dict(verdicts), usable=len(usable_rows),
                   usable_by_group=dict(Counter(r['group'] for r in usable_rows)), usable_by_verdict=dict(Counter(r['verdict'] for r in usable_rows)),
                   failed_checks=sum(1 for r in report if not r['usable'] and r['verdict'] in ('minimal', 'larger')),
                   retry_candidates=len(retry),
                   fail_reasons=dict(Counter(p.split(':')[0].split(' (')[0] for r in report if r['verdict'] in ('minimal', 'larger') for p in r['problems']).most_common(10)),
                   median_length_ratio=sorted(r['length_ratio'] for r in usable_rows)[len(usable_rows) // 2] if usable_rows else None,
                   median_char_similarity=sorted(r['char_similarity'] for r in usable_rows)[len(usable_rows) // 2] if usable_rows else None)
    args.out.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out / 'validation.jsonl', report)
    write_jsonl(args.out / 'validated.jsonl', usable_rows)
    if retry:
        write_jsonl(args.out / 'retry-input.jsonl', retry)
    (args.out / 'validation-summary.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(summary, indent=1, ensure_ascii=False))


def cmd_pairs(args):
    rows = read_jsonl(args.validated)
    # Brevity guard: the set must not teach "shorter is better". While the mean chosen/rejected word ratio is below MIN_MEAN_RATIO, drop the pair
    # with the lowest ratio (ties by id), so the rule is fixed and reproducible.
    dropped = 0
    rows.sort(key=lambda r: (r['length_ratio'], r['id']))
    while rows and sum(r['length_ratio'] for r in rows) / len(rows) < MIN_MEAN_RATIO:
        rows.pop(0)
        dropped += 1
    rows.sort(key=lambda r: r['id'])
    out = []
    for r in rows:
        out.append(dict(id=r['id'], kind=r['kind'], source='atlas', prompt=[dict(role='user', content=r['prompt'])],
                        chosen=[dict(role='assistant', content=r['chosen'])], rejected=[dict(role='assistant', content=r['rejected'])],
                        chat_template_kwargs=dict(enable_thinking=False), label='synthetic_repair', lane='turkish', group=r['group'],
                        verdict=r['verdict'], length_ratio=r['length_ratio'], char_similarity=r['char_similarity']))
    write_jsonl(args.out, out)
    print(f'{len(out)} pairs -> {args.out}', dict(Counter(r['group'] for r in out)), 'mean length ratio',
          round(sum(r['length_ratio'] for r in rows) / max(1, len(rows)), 3), f'(dropped {dropped} shortest by the brevity guard)')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('pool')
    p.add_argument('--prompts', type=Path, required=True)
    p.add_argument('--answers', type=Path, required=True)
    p.add_argument('--out-data', type=Path, required=True)
    p.add_argument('--out-local', type=Path, required=True)
    p.add_argument('--train', type=int, default=2000)
    p.add_argument('--heldout', type=int, default=200)
    p.add_argument('--pilot', type=int, default=300)
    p.add_argument('--drop-plain-after-pilot', action='store_true', help='replace the plain_source prompts after the pilot with unused constraint prompts')
    p.set_defaults(func=cmd_pool)
    v = sub.add_parser('validate')
    v.add_argument('--packet', type=Path, required=True)
    v.add_argument('--results', type=Path, nargs='+', required=True)
    v.add_argument('--accept', type=Path, required=True)
    v.add_argument('--out', type=Path, required=True)
    v.set_defaults(func=cmd_validate)
    q = sub.add_parser('pairs')
    q.add_argument('--validated', type=Path, required=True)
    q.add_argument('--out', type=Path, required=True)
    q.set_defaults(func=cmd_pairs)
    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
