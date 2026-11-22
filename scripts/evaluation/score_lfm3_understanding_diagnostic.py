"""Score understanding-diagnostic runs and compare conditions or models with item-level paired bootstrap.

  score:   python score_lfm3_understanding_diagnostic.py score --run-dir RUN [--run-dir ...]
  compare: python score_lfm3_understanding_diagnostic.py compare --run-dir RUN
Accuracy of a condition is the mean over sampling seeds per item; intervals resample items (not samples).
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import random
import re
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lfm3_eval_v2_scoring as scoring  # noqa: E402

REPLY_LANG = {'A': 'en', 'B': 'tr', 'C': 'en', 'D': 'tr', 'F': 'en', 'G': 'en'}
EN_STOP = set('the and is of to we so total then answer that this with are for each has have per step first problem'.split())
TR_STOP = set('ve bir için toplam her olarak bu ile cevap yani şimdi kadar daha olan da de mi problem adım önce'.split())
COMPARISONS = [('A', 'D', 'gap: Turkish prompt+reply vs English'), ('A', 'C', 'reading cost (reply en)'),
               ('A', 'B', 'writing cost (prompt en)'), ('C', 'D', 'reply language at fixed tr prompt'),
               ('D', 'F', 'restate-in-English gain over D'), ('D', 'G', 'translate-first gain over D'),
               ('C', 'G', 'translate-first vs direct tr prompt, English reply'), ('F', 'G', 'restate vs translate-first')]


def reply_language(text):
    words = re.findall(r'[a-zçğıöşüâî]+', text.lower())
    en, tr = sum(w in EN_STOP for w in words), sum(w in TR_STOP for w in words)
    if en + tr < 3:
        return 'none'
    return 'tr' if tr > 1.5 * en else 'en' if en > 1.5 * tr else 'mix'


def score_run(run_dir):
    manifest = json.loads((run_dir / 'run-manifest.json').read_text(encoding='utf-8'))
    thinking = manifest['thinking'] == 'on'
    translations = {}
    if (run_dir / 'translations.json').exists():
        translations = json.loads((run_dir / 'translations.json').read_text(encoding='utf-8'))
    rows = []
    for line in (run_dir / 'answers.jsonl').read_text(encoding='utf-8').splitlines():
        a = json.loads(line)
        s = scoring.score_math(a['raw_output'], a['gold'], REPLY_LANG[a['condition']], thinking)
        visible, _ = scoring.split_thinking(a['raw_output'], thinking)
        rows.append(dict(id=a['id'], pair_id=a['pair_id'], condition=a['condition'], seed=a['seed'],
                         correct=s['correct_any'], strict=s['correct_strict'], method=s['method'],
                         thinking_closed=s['thinking_closed'], tokens=a['generated_tokens'],
                         hit_max=a['hit_max_new_tokens'], reply_lang=reply_language(visible),
                         numbers_preserved=translations.get(a['pair_id'], {}).get('numbers_preserved')))
    return manifest, rows


def item_means(rows, cond, field='correct', where=lambda r: True):
    per = defaultdict(list)
    for r in rows:
        if r['condition'] == cond and where(r):
            per[r['pair_id']].append(float(r[field]))
    return {k: statistics.mean(v) for k, v in per.items()}


def boot(values, reps=4000, seed=3407):
    rng = random.Random(seed)
    n = len(values)
    means = sorted(statistics.mean(values[rng.randrange(n)] for _ in range(n)) for _ in range(reps))
    return statistics.mean(values), means[int(0.025 * reps)], means[int(0.975 * reps) - 1]


def boot_delta(x, y, reps=4000, seed=3407):
    keys = sorted(set(x) & set(y))
    diffs = [y[k] - x[k] for k in keys]
    mean, lo, hi = boot(diffs, reps, seed)
    return dict(delta=round(mean, 4), lo=round(lo, 4), hi=round(hi, 4), n=len(keys))


def summarize(manifest, rows):
    out = dict(name=manifest['name'], thinking=manifest['thinking'], seeds=manifest['seeds'], cells={}, deltas={})
    conditions = sorted({r['condition'] for r in rows})
    for cond in conditions:
        sel = [r for r in rows if r['condition'] == cond]
        mean, lo, hi = boot(list(item_means(rows, cond).values()))
        out['cells'][cond] = dict(
            accuracy=round(mean, 4), lo=round(lo, 4), hi=round(hi, 4), n_samples=len(sel),
            cap_rate=round(sum(r['hit_max'] for r in sel) / len(sel), 4),
            mean_tokens=round(statistics.mean(r['tokens'] for r in sel), 1),
            unclosed_thinking=round(sum(r['thinking_closed'] is False for r in sel) / len(sel), 4),
            reply_language=dict(Counter(r['reply_lang'] for r in sel)),
            strict_marker_rate=round(sum(r['method'] in ('marker', 'boxed') for r in sel) / len(sel), 4))
    if 'G' in conditions:
        for flag in (True, False):
            sub = item_means(rows, 'G', where=lambda r, f=flag: r['numbers_preserved'] is f)
            if sub:
                out['cells'][f'G|numbers_preserved={flag}'] = dict(items=len(sub), accuracy=round(statistics.mean(sub.values()), 4))
    for a, b, label in COMPARISONS:
        if a in conditions and b in conditions:
            out['deltas'][f'{b}-{a}'] = dict(label=label, **boot_delta(item_means(rows, a), item_means(rows, b)))
    return out


def cmd_score(args):
    for run_dir in args.run_dir:
        manifest, rows = score_run(run_dir)
        (run_dir / 'scores.jsonl').write_text('\n'.join(json.dumps(r) for r in rows) + '\n', encoding='utf-8')
        summary = summarize(manifest, rows)
        (run_dir / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n', encoding='utf-8')
        print(f'== {summary["name"]} (thinking {summary["thinking"]}, seeds {len(summary["seeds"])})')
        for cond, c in summary['cells'].items():
            if 'lo' in c:
                print(f'  {cond}: acc {c["accuracy"]:.3f} [{c["lo"]:.3f},{c["hi"]:.3f}] cap {c["cap_rate"]:.2f} '
                      f'tok {c["mean_tokens"]:.0f} unclosed {c["unclosed_thinking"]:.2f} lang {c["reply_language"]}')
            else:
                print(f'  {cond}: items {c["items"]} acc {c["accuracy"]:.3f}')
        for key, d in summary['deltas'].items():
            print(f'  delta {key} ({d["label"]}): {d["delta"]:+.3f} [{d["lo"]:+.3f},{d["hi"]:+.3f}] n={d["n"]}')


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('score')
    p.add_argument('--run-dir', type=Path, action='append', required=True)
    p.set_defaults(func=cmd_score)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
