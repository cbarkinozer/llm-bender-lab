"""SFT core v01: compare models on the 100-item GSM8K final test (EN and TR, thinking on, k samples per item).

  python compare_lfm3_sft_core_final.py --base V_base.jsonl --candidate V_model.jsonl [--candidate ...] [--out OUT.json]
        [--suspects --prompts P.jsonl]

Each verified file has rows {id: 'c-mathtest-0001-en|tr', verified:[...], tokens:[...], reasons:[...]}; other ids are ignored.
Per item accuracy = mean over samples (a sample counts only if it reached EOS and the number matches). Paired bootstrap on items.
--suspects lists items the base solves in English (>= .75) but not in Turkish (<= .25): candidates for translation errors that
change the answer (a human should read them before the final test is trusted).
"""
import argparse
import json
from pathlib import Path
import random
import statistics


def load(path):
    out = {}
    for line in Path(path).read_text(encoding='utf-8').split('\n'):
        if not line.strip():
            continue
        r = json.loads(line)
        if not r['id'].startswith('c-mathtest-'):
            continue
        core, lang = r['id'].rsplit('-', 1)
        out[(core, lang)] = dict(acc=sum(bool(v) for v in r['verified']) / len(r['verified']), tokens=r['tokens'],
                                 no_eos=sum(x == 'no_eos' for x in r['reasons']) / len(r['reasons']))
    return out


def bootstrap(diffs, n=10000, seed=3407):
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(diffs, k=len(diffs))) for _ in range(n))
    return means[int(.025 * n)], means[int(.975 * n)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, action='append', required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--suspects', action='store_true')
    parser.add_argument('--prompts', type=Path)
    args = parser.parse_args()
    base = load(args.base)
    result = {}
    for lang in ('en', 'tr'):
        items = sorted(k for k in base if k[1] == lang)
        result[f'base/{lang}'] = dict(n=len(items), acc=round(statistics.fmean(base[k]['acc'] for k in items), 4),
                                      no_eos=round(statistics.fmean(base[k]['no_eos'] for k in items), 4),
                                      median_tokens=statistics.median(t for k in items for t in base[k]['tokens']))
    for cand in args.candidate:
        c = load(cand)
        for lang in ('en', 'tr'):
            items = sorted(k for k in base if k[1] == lang and k in c)
            diffs = [c[k]['acc'] - base[k]['acc'] for k in items]
            lo, hi = bootstrap(diffs)
            result[f'{cand.stem}/{lang}'] = dict(
                n=len(items), acc=round(statistics.fmean(c[k]['acc'] for k in items), 4), delta_vs_base=round(statistics.fmean(diffs), 4),
                ci=[round(lo, 4), round(hi, 4)], no_eos=round(statistics.fmean(c[k]['no_eos'] for k in items), 4),
                median_tokens=statistics.median(t for k in items for t in c[k]['tokens']))
    print(json.dumps(result, indent=1))
    if args.out:
        args.out.write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')
    if args.suspects:
        prompts = {}
        if args.prompts:
            for line in args.prompts.read_text(encoding='utf-8').split('\n'):
                if line.strip():
                    r = json.loads(line)
                    prompts[r['id']] = r['messages'][0]['content']
        print('\nSUSPECT ITEMS (base: English >= .75, Turkish <= .25)')
        for core in sorted({k[0] for k in base}):
            if (core, 'en') in base and (core, 'tr') in base and base[(core, 'en')]['acc'] >= .75 and base[(core, 'tr')]['acc'] <= .25:
                print(f'--- {core}  EN acc {base[(core, "en")]["acc"]}  TR acc {base[(core, "tr")]["acc"]}')
                if prompts:
                    print('EN:', prompts.get(f'{core}-en', '')[:400].replace('\n', ' '))
                    print('TR:', prompts.get(f'{core}-tr', '')[:400].replace('\n', ' '))


if __name__ == '__main__':
    main()
