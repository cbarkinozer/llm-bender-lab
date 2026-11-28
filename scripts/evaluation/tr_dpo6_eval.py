"""exp-006 scoring: code-check pass rates, anti-hacking flags and paired bootstrap between arms. No model judge.

  python tr_dpo6_eval.py --prompts P.jsonl --arm parent=A1.jsonl --arm sft-control=A2.jsonl --arm dpo=A3.jsonl \
      --compare dpo:sft-control --compare dpo:parent --out report.json [--split heldout] [--boot 10000] [--seed 11]
  python tr_dpo6_eval.py selftest

Answer rows are in the sampler format (id, sample, raw_output, finish_reason). Primary metric: per prompt, the share of its samples that pass
every check; the arm score is the mean over prompts, and a comparison is the paired bootstrap (resampling prompts) of the difference.
Flags per arm: mean words, skeleton share (answers below 40% of the parent's median words), distinct 2-gram ratio, source copy rate (share of
answer 5-grams that occur in the prompt, grounded prompts only), invented-number share (grounded prompts), pass rate per constraint type.
"""
import argparse
import hashlib
import json
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'datasets'))
sys.path.insert(0, str(ROOT / 'scripts' / 'evaluation'))
import tr_dpo6_pairs as P  # noqa: E402
import tr_dpo6_checks as C  # noqa: E402


def ngrams(words, n):
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def score_arm(prompts, answers):
    """Per-prompt results for one arm: {id: [dict(ok, words, failures, text)]}"""
    by = {}
    for a in answers:
        by.setdefault(a['id'], []).append(a)
    out = {}
    for pid, row in prompts.items():
        if pid not in by:
            continue
        out[pid] = P.candidates_for(row, sorted(by[pid], key=lambda a: a['sample']))
    return out


def distinct2(texts):
    seen, total = set(), 0
    for t in texts:
        w = C.tr_words(t)
        grams = [tuple(w[i:i + 2]) for i in range(len(w) - 1)]
        seen.update(grams)
        total += len(grams)
    return len(seen) / total if total else 0.0


def flags(prompts, scored, parent_median):
    cands = [(pid, c) for pid, cs in scored.items() for c in cs]
    words = [c['words'] for _, c in cands]
    texts = [c['text'] for _, c in cands]
    grounded = [(pid, c) for pid, c in cands if prompts[pid].get('grounded')]
    copy = []
    for pid, c in grounded:
        a = C.tr_words(c['text'])
        src = ngrams(C.tr_words(prompts[pid]['prompt']), 5)
        g = [tuple(a[i:i + 5]) for i in range(len(a) - 4)]
        if g:
            copy.append(sum(x in src for x in g) / len(g))
    types = {}
    for pid, c in cands:
        for it in P.items_from_check(prompts[pid].get('check')) or []:
            t = it['type']
            fail = any(f.split(' ')[0].startswith(t.split('_')[0]) for f in c['failures'])
            types.setdefault(t, []).append(not fail)
    return dict(
        answers=len(cands), mean_words=statistics.mean(words), median_words=statistics.median(words),
        skeleton_share=sum(w < 0.4 * parent_median for w in words) / len(words) if parent_median else None,
        distinct_2gram=distinct2(texts), source_copy_rate=statistics.mean(copy) if copy else None,
        invented_share=(sum(any(f.startswith('invented') for f in c['failures']) for _, c in grounded) / len(grounded)) if grounded else None,
        not_ended_share=sum('not ended' in c['failures'] for _, c in cands) / len(cands),
        pass_rate_by_type={t: sum(v) / len(v) for t, v in sorted(types.items())})


def per_prompt_rates(scored):
    return {pid: sum(c['ok'] for c in cs) / len(cs) for pid, cs in scored.items()}


def paired_bootstrap(a, b, boot, seed):
    ids = sorted(set(a) & set(b))
    diffs = [a[i] - b[i] for i in ids]
    rng = random.Random(seed)
    n = len(diffs)
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(boot))
    return dict(prompts=n, difference=sum(diffs) / n, ci95=[means[int(0.025 * boot)], means[int(0.975 * boot) - 1]],
                prompts_better=sum(d > 0 for d in diffs), prompts_worse=sum(d < 0 for d in diffs))


def selftest():
    prompts = {'p1': dict(id='p1', prompt='Kısa yaz.', check=dict(items=[dict(type='max_words', n=5)]), split='heldout'),
               'p2': dict(id='p2', prompt='Kısa yaz.', check=dict(items=[dict(type='max_words', n=5)]), split='heldout')}
    mk = lambda pid, k, text: dict(id=pid, sample=k, raw_output=text + '<|im_end|>', finish_reason='eos')
    good = [mk('p1', 0, 'Evet tamam.'), mk('p1', 1, 'Evet tamam.'), mk('p2', 0, 'Evet.'), mk('p2', 1, 'Evet.')]
    bad = [mk('p1', 0, 'bir iki üç dört beş altı yedi sekiz.'), mk('p1', 1, 'Evet tamam.'), mk('p2', 0, 'bir iki üç dört beş altı yedi sekiz.'),
           mk('p2', 1, 'bir iki üç dört beş altı yedi sekiz.')]
    g, b = per_prompt_rates(score_arm(prompts, good)), per_prompt_rates(score_arm(prompts, bad))
    assert g == dict(p1=1.0, p2=1.0) and b == dict(p1=0.5, p2=0.0), (g, b)
    r = paired_bootstrap(g, b, 500, 1)
    assert abs(r['difference'] - 0.75) < 1e-9 and r['ci95'][0] > 0 and r['prompts_better'] == 2, r
    f = flags(prompts, score_arm(prompts, bad), 8)
    assert f['answers'] == 4 and f['pass_rate_by_type']['max_words'] == 0.25, f
    print('selftest passed')


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'selftest':
        return selftest()
    ap = argparse.ArgumentParser()
    ap.add_argument('--prompts', type=Path, required=True)
    ap.add_argument('--arm', action='append', default=[], help='NAME=answers.jsonl')
    ap.add_argument('--compare', action='append', default=[], help='A:B  (difference A minus B)')
    ap.add_argument('--split', default=None)
    ap.add_argument('--boot', type=int, default=10000)
    ap.add_argument('--seed', type=int, default=11)
    ap.add_argument('--parent', default='parent')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    prompts = {r['id']: r for r in P.read_jsonl(args.prompts) if not args.split or r.get('split') == args.split}
    arms = {}
    for spec in args.arm:
        name, path = spec.split('=', 1)
        arms[name] = (Path(path), score_arm(prompts, P.read_jsonl(path)))
    assert args.parent in arms, 'the parent arm is needed for the skeleton flag'
    parent_median = statistics.median(c['words'] for cs in arms[args.parent][1].values() for c in cs)
    rates = {n: per_prompt_rates(s) for n, (_, s) in arms.items()}
    report = dict(prompts_file=str(args.prompts), prompts_sha256=hashlib.sha256(args.prompts.read_bytes()).hexdigest(), split=args.split,
                  prompts=len(prompts), boot=args.boot, seed=args.seed, parent_median_words=parent_median, arms={}, comparisons={})
    for n, (path, s) in arms.items():
        report['arms'][n] = dict(answers_file=str(path), answers_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), prompts_scored=len(s),
                                 pass_rate=statistics.mean(rates[n].values()), **flags(prompts, s, parent_median))
    for spec in args.compare:
        a, b = spec.split(':')
        report['comparisons'][spec] = paired_bootstrap(rates[a], rates[b], args.boot, args.seed)
    args.out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({n: round(x['pass_rate'], 4) for n, x in report['arms'].items()}), json.dumps(report['comparisons']))


if __name__ == '__main__':
    main()
