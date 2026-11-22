"""SFT core v01: evaluate the pre-registered gates of exp-019/exp-020 from downloaded run directories (CPU, local).

  python gates_lfm3_sft_core.py --results RESULTS_DIR --name exp019 --out gates.json
RESULTS_DIR holds the extracted run directories (diag-runs, belebele-runs, turblimp, writing-runs, guard-runs, runs) and
baselines/diag-{base,selfdistill-b-cpt}-think-on-scores.jsonl. Rules: experiments/.../exp-019-sft-core-pack/README.md.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import random
import re
import statistics

EN_STOP = {'the', 'and', 'is', 'of', 'to', 'in', 'that', 'it', 'for', 'with', 'as', 'was', 'are', 'this', 'be', 'you', 'have', 'i'}
TR_LETTERS = re.compile('[çğıöşüÇĞİÖŞÜ]')
WORD = re.compile(r"[A-Za-zçğıöşüÇĞİÖŞÜ]+")
CELLS = 'ABCDFG'


def rd(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').split('\n') if s.strip()]


def per_item(path, condition):
    acc = defaultdict(list)
    for r in rd(path):
        if r['condition'] == condition:
            acc[r['pair_id']].append(1.0 if r['correct'] else 0.0)
    return {k: statistics.fmean(v) for k, v in acc.items()}


def boot(diffs, n=10000, seed=3407):
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(diffs, k=len(diffs))) for _ in range(n))
    return round(means[int(.025 * n)], 4), round(means[int(.975 * n)], 4)


def paired(a, b):
    keys = sorted(set(a) & set(b))
    diffs = [a[k] - b[k] for k in keys]
    lo, hi = boot(diffs)
    return dict(delta=round(statistics.fmean(diffs), 4), ci=[lo, hi], n=len(keys))


def english_answer(raw):
    text = raw.split('</think>')[-1]
    words = [w.lower() for w in WORD.findall(text)]
    if len(words) < 8:
        return False
    en = sum(w in EN_STOP for w in words) / len(words)
    diacritics = len(TR_LETTERS.findall(text)) / max(1, sum(len(w) for w in words))
    return en >= 0.08 and diacritics < 0.01


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    R, name = args.results, args.name
    base_scores = R / 'baselines/diag-base-think-on-scores.jsonl'
    armb_scores = R / 'baselines/diag-selfdistill-b-cpt-think-on-scores.jsonl'
    own_scores = R / f'diag-runs/{name}-think-on/scores.jsonl'
    out = {}
    cells = {}
    for c in CELLS:
        base, armb, own = per_item(base_scores, c), per_item(armb_scores, c), per_item(own_scores, c)
        cells[c] = dict(base=round(statistics.fmean(base.values()), 4), armB=round(statistics.fmean(armb.values()), 4),
                        model=round(statistics.fmean(own.values()), 4), vs_base=paired(own, base), vs_armB=paired(own, armb))
    out['diagnostic_cells_thinking_on'] = cells
    d = cells['D']
    out['G1'] = dict(rule='D: model - base >= -0.03 and lower bound of (model - armB) > 0', D=d,
                     passed=bool(d['vs_base']['delta'] >= -0.03 and d['vs_armB']['ci'][0] > 0))
    bel = json.loads((R / f'belebele-runs/{name}/summary.json').read_text(encoding='utf-8'))
    tr = bel['tr']['restricted_acc']
    out['G3'] = dict(rule='Belebele TR restricted >= .45 and >= armB (.483) - .03', tr_restricted=tr, en_restricted=bel['en']['restricted_acc'],
                     passed=bool(tr >= 0.45 and tr >= 0.483 - 0.03))
    tb = json.loads((R / f'turblimp/{name}/scores.json').read_text(encoding='utf-8'))
    out['G4'] = dict(rule='TurBLiMP macro accuracy >= .85', macro=tb['macro_accuracy'], passed=bool(tb['macro_accuracy'] >= 0.85))
    answers = rd(R / f'writing-runs/{name}/answers.jsonl')
    english = [a['id'] for a in answers if english_answer(a['raw_output'])]
    no_eos = sum(a['finish_reason'] != 'eos' for a in answers)
    out['G5'] = dict(rule='at most 1 of 40 answers entirely in English (heuristic)', english_answers=english, no_eos=no_eos,
                     passed=len(english) <= 1)
    guard = json.loads((R / f'guard-runs/{name}/compare-vs-base.json').read_text(encoding='utf-8'))
    full = json.loads((R / f'guard-runs/{name}/compare-full-ifeval.json').read_text(encoding='utf-8'))
    out['G6'] = dict(rule='exp-018 rule, thinking on: IFEval strict (270) and HumanEval', ifeval_on=guard['ifeval_strict|on'],
                     humaneval_on=guard['humaneval|on'], passed=guard['ifeval_strict|on']['verdict'] == 'PASS' and guard['humaneval|on']['verdict'] == 'PASS',
                     reported_not_gating=dict(ifeval_strict_off_full541=full['ifeval_strict|off'], humaneval_off=guard['humaneval|off'],
                                              ifeval_strict_off_270=guard['ifeval_strict|off']))
    out['G7_note'] = 'tools and English math come from the eval v2 comparison logs (see README table)'
    print(json.dumps(out, indent=1, ensure_ascii=False))
    if args.out:
        args.out.write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
