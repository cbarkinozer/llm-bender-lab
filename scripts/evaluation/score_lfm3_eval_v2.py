"""Score eval v2 generations and compare runs with paired statistics.

score:   python score_lfm3_eval_v2.py score --run-dir RUN [--run-dir ...]
compare: python score_lfm3_eval_v2.py compare --base RUN_A --candidate RUN_B
A run dir holds answers-seed<N>.jsonl and run-manifest.json written by run_lfm3_eval_v2.py.
Per-item results are kept (scores-seed<N>.jsonl) so every number can be re-derived or audited.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lfm3_eval_v2_scoring as scoring  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / 'experiments/turkish-capability/lfm3-1.7b/eval-v2'
PACKET_FILES = {'math': 'math-pairs.jsonl', 'symbolic': 'symbolic-pairs.jsonl', 'toolcall': 'toolcall-pairs.jsonl'}


def load_packets(data_dir, manifest):
    rows = {}
    for entry in manifest['packets']:
        blob = (data_dir / entry['file']).read_bytes()
        if hashlib.sha256(blob).hexdigest() != entry['sha256']:
            raise ValueError(f'Packet checksum mismatch: {entry["file"]}')
        for line in blob.decode('utf-8').splitlines():
            row = json.loads(line)
            rows[row['id']] = row
    return rows


def score_row(row, answer, thinking):
    raw, lang = answer['raw_output'], row['language']
    if row['family'] == 'math':
        result = scoring.score_math(raw, row['gold'], lang, thinking)
        primary = result['correct_any']
    elif row['family'] == 'symbolic':
        result = scoring.score_symbolic(raw, row['gold'], lang, thinking)
        primary = result['correct']
    elif row['family'] == 'toolcall':
        result = scoring.score_toolcall(raw, row['gold_calls'], row['tools'], thinking)
        primary = result['correct']
    else:
        raise ValueError(row['family'])
    return {**result, **dict(id=row['id'], pair_id=row['pair_id'], family=row['family'],
                             subfamily=row.get('subfamily'), language=lang, correct=bool(primary),
                             generated_tokens=answer.get('generated_tokens'),
                             finish_reason=answer.get('finish_reason'),
                             hit_max_new_tokens=answer.get('hit_max_new_tokens'))}


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(centre - half, 4), round(centre + half, 4))


def summarize(scores):
    out = {}
    groups = defaultdict(list)
    for s in scores:
        groups[(s['family'], s['language'])].append(s)
    for (family, lang), items in sorted(groups.items()):
        k, n = sum(i['correct'] for i in items), len(items)
        entry: dict = dict(n=n, correct=k, accuracy=round(k / n, 4), wilson95=wilson(k, n),
                     mean_tokens=round(statistics.mean(i['generated_tokens'] or 0 for i in items), 1),
                     median_tokens=statistics.median(i['generated_tokens'] or 0 for i in items),
                     hit_max_rate=round(sum(bool(i['hit_max_new_tokens']) for i in items) / n, 4),
                     eos_rate=round(sum(i['finish_reason'] == 'eos' for i in items) / n, 4))
        closed = [i['thinking_closed'] for i in items if i['thinking_closed'] is not None]
        if closed:
            entry['thinking_closure_rate'] = round(sum(closed) / len(closed), 4)
        if family == 'math':
            entry['strict_accuracy'] = round(sum(i['correct_strict'] for i in items) / n, 4)
            entry['marker_parse_rate'] = round(sum(i['method'] in ('marker', 'boxed') for i in items) / n, 4)
        if family == 'symbolic':
            entry['number_only_rate'] = round(sum(i['number_only'] for i in items) / n, 4)
        if family == 'toolcall':
            entry['errors'] = dict(Counter(i['error'] for i in items if not i['correct']))
            entry['by_subfamily'] = {sub: round(sum(i['correct'] for i in items if i['subfamily'] == sub)
                                                / max(1, sum(i['subfamily'] == sub for i in items)), 4)
                                     for sub in sorted({i['subfamily'] for i in items})}
        out[f'{family}/{lang}'] = entry
    return out


def paired_vectors(scores_a, scores_b):
    index_a = {s['id']: s['correct'] for s in scores_a}
    return [(index_a[s['id']], s['correct']) for s in scores_b if s['id'] in index_a]


def mcnemar_exact(b01, b10):
    n = b01 + b10
    if n == 0:
        return 1.0
    k = min(b01, b10)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n * 2
    return round(min(1.0, p), 4)


def bootstrap_delta(pairs, seed=3407, reps=5000):
    rng = random.Random(seed)
    n = len(pairs)
    deltas = []
    for _ in range(reps):
        sample = [pairs[rng.randrange(n)] for _ in range(n)]
        deltas.append(sum(b - a for a, b in sample) / n)
    deltas.sort()
    return (round(deltas[int(.025 * reps)], 4), round(deltas[int(.975 * reps)], 4))


def compare(base_scores, cand_scores):
    out = {}
    keys = sorted({(s['family'], s['language']) for s in cand_scores})
    for family, lang in keys:
        a = [s for s in base_scores if s['family'] == family and s['language'] == lang]
        b = [s for s in cand_scores if s['family'] == family and s['language'] == lang]
        pairs = paired_vectors(a, b)
        if not pairs:
            continue
        gain = sum((not x) and y for x, y in pairs)
        loss = sum(x and (not y) for x, y in pairs)
        delta = sum(y - x for x, y in pairs) / len(pairs)
        out[f'{family}/{lang}'] = dict(n=len(pairs), base=round(sum(x for x, _ in pairs) / len(pairs), 4),
                                        candidate=round(sum(y for _, y in pairs) / len(pairs), 4),
                                        delta=round(delta, 4), bootstrap95=bootstrap_delta(pairs),
                                        gained=gain, lost=loss, mcnemar_p=mcnemar_exact(gain, loss))
    return out


def tr_en_gap(scores):
    """Paired TR minus EN accuracy per family (pairs share pair_id)."""
    gaps = {}
    for family in sorted({s['family'] for s in scores}):
        by_pair = defaultdict(dict)
        for s in scores:
            if s['family'] == family:
                by_pair[s['pair_id']][s['language']] = s['correct']
        pairs = [(v['en'], v['tr']) for v in by_pair.values() if 'en' in v and 'tr' in v]
        if pairs:
            gaps[family] = dict(n=len(pairs), en=round(sum(x for x, _ in pairs) / len(pairs), 4),
                                tr=round(sum(y for _, y in pairs) / len(pairs), 4),
                                tr_minus_en=round(sum(y - x for x, y in pairs) / len(pairs), 4),
                                bootstrap95=bootstrap_delta(pairs))
    return gaps


def score_run(run_dir, data_dir, manifest):
    packets = load_packets(data_dir, manifest)
    run = json.loads((run_dir / 'run-manifest.json').read_text(encoding='utf-8'))
    thinking = run['thinking'] == 'on'
    result = {}
    for answers_path in sorted(run_dir.glob('answers-seed*.jsonl')):
        seed = answers_path.stem.split('seed')[1]
        answers = [json.loads(line) for line in answers_path.read_text(encoding='utf-8').splitlines()]
        ids = [a['id'] for a in answers]
        if len(ids) != len(set(ids)):
            raise ValueError(f'Duplicate ids in {answers_path}')
        scores = [score_row(packets[a['id']], a, thinking) for a in answers]
        with (run_dir / f'scores-seed{seed}.jsonl').open('w', encoding='utf-8') as f:
            for s in scores:
                f.write(json.dumps(s, ensure_ascii=False, default=str) + '\n')
        result[seed] = dict(summary=summarize(scores), tr_en_gap=tr_en_gap(scores), items=len(scores))
    summary = dict(run=run.get('name'), thinking=run['thinking'], scorer=scoring.SCORER_VERSION, seeds=result)
    (run_dir / 'summary.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    return summary


def load_scores(run_dir):
    rows = []
    for path in sorted(run_dir.glob('scores-seed*.jsonl')):
        rows.extend(json.loads(line) for line in path.read_text(encoding='utf-8').splitlines())
    return rows


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    s = sub.add_parser('score')
    s.add_argument('--run-dir', type=Path, action='append', required=True)
    s.add_argument('--data-dir', type=Path, default=EXP / 'data-local')
    c = sub.add_parser('compare')
    c.add_argument('--base', type=Path, required=True)
    c.add_argument('--candidate', type=Path, required=True)
    c.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.command == 'score':
        manifest = json.loads((EXP / 'manifest-core.json').read_text(encoding='utf-8'))
        for run_dir in args.run_dir:
            print(json.dumps(score_run(run_dir, args.data_dir, manifest), indent=1, ensure_ascii=False))
    else:
        result = compare(load_scores(args.base), load_scores(args.candidate))
        text = json.dumps(result, indent=1, ensure_ascii=False)
        if args.output:
            args.output.write_text(text + '\n', encoding='utf-8')
        print(text)


if __name__ == '__main__':
    main()
