"""Guard table for exp-005: paired comparison of two arms against exp-021 on the registered guards (decision rule 5).

  python tr_dpo_guards_table.py --root RESULTS_DIR --out guards.json
RESULTS_DIR holds guard-runs/, belebele-runs/, turblimp/, runs/, sft-core/ as fetched from the pod (names exp021, exp005-dpo-on-sft, exp005-sft-only).

IFEval (strict, thinking off: the 270 and the 271 other prompts together; thinking on: 270) and HumanEval are compared item by item with an exact
McNemar test and a paired 95% interval of the accuracy difference (normal approximation on the discordant pairs); "within the noise" in rule 5 is
read here as: the paired interval contains 0. Belebele (restricted accuracy, the metric used for the earlier 48.7 / 70.0 numbers) and TurBLiMP macro
accuracy are compared as point differences against the registered 1 point limit, with the published intervals alongside.
"""
import argparse
import json
import math
from pathlib import Path

MODELS = ['exp021', 'exp005-dpo-on-sft', 'exp005-sft-only']


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def items(root, model, task, mode, field, include_rest=False):
    out = {}
    dirs = [root / 'guard-runs' / model] + ([root / 'guard-runs' / f'{model}-rest'] if include_rest else [])
    for d in dirs:
        for r in read_jsonl(d / 'scores.jsonl'):
            if r['task'] == task and r['thinking'] == mode:
                out[r['id']] = bool(r[field])
    return out


def mcnemar(a, b):
    ids = sorted(set(a) & set(b))
    only_a = sum(a[i] and not b[i] for i in ids)
    only_b = sum(b[i] and not a[i] for i in ids)
    n, k = only_a + only_b, min(only_a, only_b)
    p = 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, j) for j in range(k + 1)) / 2 ** n)
    diff = (only_b - only_a) / len(ids)  # b minus a
    se = math.sqrt(max(only_a + only_b - (only_b - only_a) ** 2 / len(ids), 0)) / len(ids)
    return dict(n=len(ids), base=sum(a[i] for i in ids) / len(ids), cand=sum(b[i] for i in ids) / len(ids), diff=diff,
                ci95=[diff - 1.96 * se, diff + 1.96 * se], only_base=only_a, only_cand=only_b, mcnemar_p=p)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root = args.root
    report = {}
    tasks = [('ifeval_strict_off', 'ifeval', 'off', 'ifeval_strict', True), ('ifeval_strict_on', 'ifeval', 'on', 'ifeval_strict', False),
             ('humaneval_off', 'humaneval', 'off', 'humaneval', False), ('humaneval_on', 'humaneval', 'on', 'humaneval', False)]
    for name, task, mode, field, rest in tasks:
        base = items(root, 'exp021', task, mode, field, rest)
        for m in MODELS[1:]:
            report.setdefault(name, {})[m] = mcnemar(base, items(root, m, task, mode, field, rest))
    bel = {m: json.loads((root / 'belebele-runs' / m / 'summary.json').read_text()) for m in MODELS}
    report['belebele'] = {m: {lang: dict(restricted=bel[m][lang]['restricted_acc'], restricted_ci=bel[m][lang]['restricted_ci'],
                                          generated=bel[m][lang]['generated_acc'], restricted_diff_vs_exp021=bel[m][lang]['restricted_acc'] - bel['exp021'][lang]['restricted_acc'])
                              for lang in ('en', 'tr')} for m in MODELS}
    turb = {m: json.loads((root / 'turblimp' / m / 'scores.json').read_text()) for m in MODELS}
    report['turblimp_macro'] = {m: dict(macro=turb[m]['macro_accuracy'], diff_vs_exp021=turb[m]['macro_accuracy'] - turb['exp021']['macro_accuracy']) for m in MODELS}
    fin = {m: json.loads((root / 'sft-core' / f'verified-{m}-final.summary.json').read_text())['math_final_test/on'] for m in MODELS}
    report['final_test_math_thinking_on'] = {m: dict(group_rate=fin[m]['group_rate'], sample_rate=fin[m]['sample_rate']) for m in MODELS}
    ev = {}
    for m in MODELS:
        s = json.loads((root / 'runs' / f'{m}-think-on' / 'summary.json').read_text())['seeds']['3407']['summary']
        ev[m] = {f'{t}_{lang}': s[f'{t}/{lang}']['accuracy'] for t in ('math', 'symbolic', 'toolcall') for lang in ('en', 'tr')}
    report['evalv2_thinking_on'] = ev
    args.out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    pct = lambda x: f'{100 * x:5.1f}'  # noqa: E731
    print('paired guards (candidate minus exp-021), points; interval = paired 95%, p = exact McNemar')
    for name, d in report.items():
        if name in ('ifeval_strict_off', 'ifeval_strict_on', 'humaneval_off', 'humaneval_on'):
            for m, v in d.items():
                print(f'{name:18} {m:18} n={v["n"]:3} base {pct(v["base"])} cand {pct(v["cand"])} diff {100 * v["diff"]:+5.1f} [{100 * v["ci95"][0]:+5.1f}, {100 * v["ci95"][1]:+5.1f}] p={v["mcnemar_p"]:.2f}')
    for lang in ('en', 'tr'):
        print(f'belebele {lang} restricted: ' + ', '.join(f'{m} {pct(report["belebele"][m][lang]["restricted"])} ({100 * report["belebele"][m][lang]["restricted_diff_vs_exp021"]:+.1f})' for m in MODELS))
    print('turblimp macro: ' + ', '.join(f'{m} {pct(v["macro"])} ({100 * v["diff_vs_exp021"]:+.1f})' for m, v in report['turblimp_macro'].items()))
    print('final test math (on): ' + ', '.join(f'{m} group {pct(v["group_rate"])} sample {pct(v["sample_rate"])}' for m, v in report['final_test_math_thinking_on'].items()))
    for key in sorted(ev['exp021']):
        print(f'evalv2 {key:14}: ' + ', '.join(f'{m} {pct(ev[m][key])}' for m in MODELS))


if __name__ == '__main__':
    main()
