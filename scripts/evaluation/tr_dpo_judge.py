"""Blind pairwise judging tooling for exp-005 (instructions: experiments/preference-rl/lfm3-1.7b/exp-005-dpo-repaired-turkish/data/JUDGE-GUIDE.md).

  sheets        build anonymised, order-randomised sheets (markdown, 25 items per batch) and the key for one comparison set
  sanity-input  turn N random training pairs (chosen against rejected) into two answer files, to test the judging procedure itself
  unblind       apply the key to the saved judgment files, print and write the report (wins, ties, Wilson interval, splits, position check)

  python tr_dpo_judge.py sheets --prompts P --a ANSWERS_A --b ANSWERS_B --name-a dpo-on-sft --name-b exp-021 --set A --seed S --out-dir DIR
  python tr_dpo_judge.py unblind --key DIR/judge-key-A.json --judgments DIR/judge-A-batch-*.jsonl --prompts P --out DIR/judge-report-A.json

Answer files use the sampler's format (id, sample, raw_output); sample 0 is the one judged. The key is never needed to judge: do not open it before
every batch of the set has a saved judgment file.
"""
import argparse
import collections
import hashlib
import json
import math
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'datasets'))
from tr_dpo_flags import read_jsonl, visible, words  # noqa: E402

CRITERIA = {0, 1, 2, 3, 4}  # JUDGE-GUIDE.md: 1 data, 2 task and limits, 3 Turkish, 4 padding; 0 for a tie
WINNERS = {'A', 'B', 'tie'}


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normal(text):
    return re.sub(r'\s+', ' ', text).strip()


def wilson(wins, n, z=1.96):
    if n == 0:
        return None, None
    p = wins / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def answers_by_id(path):
    out = {}
    for r in read_jsonl(path):
        if r.get('sample', 0) == 0:
            assert r['id'] not in out, f'two sample-0 answers for {r["id"]} in {path}'
            out[r['id']] = visible(r['raw_output'])
    return out


def fence(text):
    longest = max((len(m) for m in re.findall(r'~+', text)), default=0)
    return '~' * max(3, longest + 1)


def block(text):
    f = fence(text)
    return f'{f}text\n{text}\n{f}\n'


def cmd_sheets(args):
    prompts = {r['id']: r for r in read_jsonl(args.prompts)}
    a, b = answers_by_id(args.a), answers_by_id(args.b)
    assert set(a) == set(b) == set(prompts), f'ids differ: prompts {len(prompts)}, a {len(a)}, b {len(b)}'
    identical = sorted(i for i in prompts if normal(a[i]) == normal(b[i]))
    items = []
    for i in sorted(prompts):
        if i in identical:
            continue
        h = hashlib.sha256(f'{args.seed}|{args.set}|{i}'.encode()).hexdigest()
        a_first = int(h[:8], 16) % 2 == 0  # which system sits in position A
        pa, pb = (a[i], b[i]) if a_first else (b[i], a[i])
        items.append(dict(id=i, order=h, prompt=prompts[i]['prompt'], A=pa, B=pb,
                          key=dict(A=args.name_a if a_first else args.name_b, B=args.name_b if a_first else args.name_a,
                                   words_A=len(words(pa)), words_B=len(words(pb)))))
    items.sort(key=lambda x: x['order'])
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for n in range(0, len(items), args.batch):
        chunk = items[n:n + args.batch]
        lines = [f'# Judge sheet, set {args.set}, batch {n // args.batch + 1:02d} ({len(chunk)} items)\n']
        for k, it in enumerate(chunk, 1):
            lines += [f'## {k}. id: {it["id"]}\n', '### Prompt\n', block(it['prompt']),
                      f'### Answer A ({len(words(it["A"]))} words)\n', block(it['A']),
                      f'### Answer B ({len(words(it["B"]))} words)\n', block(it['B'])]
        (args.out_dir / f'judge-sheet-{args.set}-batch-{n // args.batch + 1:02d}.md').write_text('\n'.join(lines), encoding='utf-8', newline='\n')
    key = dict(set=args.set, seed=args.seed, name_a=args.name_a, name_b=args.name_b, prompts=len(prompts), identical=identical,
               batches=math.ceil(len(items) / args.batch), batch_size=args.batch, order=[it['id'] for it in items],
               items={it['id']: it['key'] for it in items}, prompts_sha256=sha256_file(args.prompts),
               answers_a_sha256=sha256_file(args.a), answers_b_sha256=sha256_file(args.b))
    (args.out_dir / f'judge-key-{args.set}.json').write_text(json.dumps(key, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(f'set {args.set}: {len(items)} items in {key["batches"]} batches, {len(identical)} identical answers (tie by code)')


def cmd_sanity_input(args):
    rows = read_jsonl(args.pairs)
    rng = random.Random(args.seed)
    pick = rng.sample(rows, args.n)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    pr, ch, rj = [], [], []
    for r in pick:
        user = [m for m in r['prompt'] if m['role'] == 'user'][-1]['content']
        pr.append(dict(id=r['id'], group=r.get('group'), prompt=user))
        ch.append(dict(id=r['id'], sample=0, raw_output=r['chosen'][0]['content']))
        rj.append(dict(id=r['id'], sample=0, raw_output=r['rejected'][0]['content']))
    for name, rows_ in (('prompts', pr), ('chosen', ch), ('rejected', rj)):
        (args.out_dir / f'sanity-{name}.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in rows_), encoding='utf-8', newline='\n')
    print(f'{len(pick)} training pairs written to {args.out_dir}')


def cmd_unblind(args):
    key = json.loads(args.key.read_text(encoding='utf-8'))
    groups = {r['id']: r.get('group') for r in read_jsonl(args.prompts)}
    got = {}
    for path in args.judgments:
        for r in read_jsonl(path):
            assert r['id'] not in got, f'two judgments for {r["id"]}'
            # null criterion = a supplied read that did not record one (owner read set O); counted in the win share, left out of the criterion split
            assert r['winner'] in WINNERS and (r['deciding_criterion'] in CRITERIA or r['deciding_criterion'] is None) and r.get('note'), f'bad judgment {r}'
            assert (r['winner'] == 'tie') == (r['deciding_criterion'] == 0), f'deciding_criterion must be 0 exactly for ties: {r}'
            got[r['id']] = r
    missing, extra = set(key['items']) - set(got), set(got) - set(key['items'])
    assert not missing and not extra, f'judgments do not match the key: missing {len(missing)}, extra {len(extra)}'
    na, nb = key['name_a'], key['name_b']
    wins, ties = collections.Counter(), 0
    by_group, by_tier, position = collections.defaultdict(collections.Counter), collections.Counter(), collections.Counter()
    shorter_wins, with_length, matched = 0, 0, collections.Counter()  # length split: how often the shorter answer wins; win share where lengths are close
    for i, r in got.items():
        g = groups.get(i)
        if r['winner'] == 'tie':
            ties += 1
            by_group[g]['tie'] += 1
            continue
        winner = key['items'][i][r['winner']]
        wins[winner] += 1
        by_group[g][winner] += 1
        by_tier[(winner, r['deciding_criterion'])] += 1
        position[r['winner']] += 1
        k = key['items'][i]
        if k.get('words_A') is not None and k['words_A'] != k['words_B']:
            with_length += 1
            shorter_wins += (k['words_A'] < k['words_B']) == (r['winner'] == 'A')
        if k.get('words_A') is not None and 0.75 <= k['words_A'] / max(1, k['words_B']) <= 1 / 0.75:
            matched['n'] += 1
            matched['first'] += winner == na
    n = wins[na] + wins[nb]
    lo, hi = wilson(wins[na], n)
    share = wins[na] / n if n else None
    report = dict(set=key['set'], names=[na, nb], items_judged=len(got), identical_by_code=len(key['identical']), ties=ties, decisive=n,
                  wins={na: wins[na], nb: wins[nb]}, win_share_first=share, wilson95=[lo, hi],
                  passes_60_and_lower_above_50=bool(share is not None and lo is not None and share >= 0.60 and lo > 0.5),
                  by_group={str(g): dict(c) for g, c in by_group.items()},
                  by_deciding_criterion={f'{w}:{c}': n_ for (w, c), n_ in sorted(by_tier.items(), key=lambda kv: (kv[0][0], str(kv[0][1])))},
                  position_share_A_among_decisive=(position['A'] / n if n else None),
                  position_warning=bool(n and not 0.40 <= position['A'] / n <= 0.60),
                  length_split=dict(decisive_with_different_lengths=with_length, shorter_answer_wins=shorter_wins,
                                    shorter_wins_share=(shorter_wins / with_length if with_length else None),
                                    length_matched_decisive=matched['n'], length_matched_first_wins=matched['first'],
                                    length_matched_win_share_first=(matched['first'] / matched['n'] if matched['n'] else None),
                                    length_matched_wilson95=wilson(matched['first'], matched['n']),
                                    note='length matched = word counts within a factor of 0.75-1.33; a reported robustness split, not a decision rule'),
                  key_sha256=sha256_file(args.key), judgment_files=[str(p) for p in args.judgments])
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('sheets')
    s.add_argument('--prompts', type=Path, required=True)
    s.add_argument('--a', type=Path, required=True, help='answers of the system named by --name-a')
    s.add_argument('--b', type=Path, required=True)
    s.add_argument('--name-a', required=True)
    s.add_argument('--name-b', required=True)
    s.add_argument('--set', required=True)
    s.add_argument('--seed', required=True)
    s.add_argument('--out-dir', type=Path, required=True)
    s.add_argument('--batch', type=int, default=25)
    s.set_defaults(fn=cmd_sheets)
    t = sub.add_parser('sanity-input')
    t.add_argument('--pairs', type=Path, required=True)
    t.add_argument('--n', type=int, default=30)
    t.add_argument('--seed', default='exp005-sanity')
    t.add_argument('--out-dir', type=Path, required=True)
    t.set_defaults(fn=cmd_sanity_input)
    u = sub.add_parser('unblind')
    u.add_argument('--key', type=Path, required=True)
    u.add_argument('--judgments', type=Path, nargs='+', required=True)
    u.add_argument('--prompts', type=Path, required=True)
    u.add_argument('--out', type=Path, required=True)
    u.set_defaults(fn=cmd_unblind)
    args = ap.parse_args()
    args.fn(args)


if __name__ == '__main__':
    main()
