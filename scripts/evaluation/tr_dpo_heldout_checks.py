"""Code-checked side checks for exp-005 (decision rule 3) on held-out answers of several systems, one table.

  python tr_dpo_heldout_checks.py --prompts heldout-prompts.jsonl --accept accept-words.txt --out DIR \
      --answers exp-021=PATH dpo-on-sft=PATH sft-only=PATH

Per system and per sample index (0 = temperature 0.1, the judged answer; 1 = temperature 0.7, the sensitivity check): answers, mean words,
share that ended with the end token, constraint pass rate (raw, and after the same number/list-marker normalisation the repair validator used),
detector flagged share (severity > 0 in tr_dpo_flags), and the flags by type. Needs Zeyrek and wordfreq (the merge venv).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'datasets'))
import tr_dpo_flags as F  # noqa: E402
import tr_dpo_repair as R  # noqa: E402


def summarize(rows, prompts, analyzer, accept):
    per = []
    for a in rows:
        p = prompts[a['id']]
        text = F.visible(a['raw_output'])
        flags = F.flags_for(analyzer, p, text, a['finish_reason'] == 'eos', accept=accept)
        raw_fail = bool(flags['constraint'])
        norm_fail = bool(F.flags_for(analyzer, p, R.normalized(text), True, accept=accept)['constraint']) if raw_fail else False
        per.append(dict(id=a['id'], group=p.get('group'), words=len(F.words(text)), ended=a['finish_reason'] == 'eos', flagged=flags['severity'] > 0,
                        checked=bool(p.get('check')), raw_fail=raw_fail, norm_fail=norm_fail, flags={k: bool(flags[k]) for k in
                        ('unfinished', 'empty', 'english_reply', 'loop', 'constraint', 'unknown_words', 'english_words')}))
    n = len(per)
    checked = [r for r in per if r['checked']]
    return dict(answers=n, mean_words=sum(r['words'] for r in per) / n, ended_share=sum(r['ended'] for r in per) / n,
                constraint_checked=len(checked),
                constraint_pass_raw=(sum(not r['raw_fail'] for r in checked) / len(checked)) if checked else None,
                constraint_pass_normalized=(sum(not r['norm_fail'] for r in checked) / len(checked)) if checked else None,
                flagged_share=sum(r['flagged'] for r in per) / n,
                flags={k: sum(r['flags'][k] for r in per) for k in per[0]['flags']},
                by_group={g: dict(answers=sum(r['group'] == g for r in per), mean_words=sum(r['words'] for r in per if r['group'] == g) / max(1, sum(r['group'] == g for r in per)),
                                  flagged_share=sum(r['flagged'] for r in per if r['group'] == g) / max(1, sum(r['group'] == g for r in per)))
                          for g in sorted({r['group'] for r in per})}), per


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--prompts', type=Path, required=True)
    ap.add_argument('--accept', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--answers', nargs='+', required=True, help='NAME=PATH of an answers.jsonl in the sampler format')
    args = ap.parse_args()
    prompts = {r['id']: r for r in F.read_jsonl(args.prompts)}
    accept = {w.strip() for w in args.accept.read_text(encoding='utf-8').splitlines() if w.strip() and not w.startswith('#')}
    analyzer = F.nonword.Analyzer()
    args.out.mkdir(parents=True, exist_ok=True)
    report, per_answer = {}, {}
    for spec in args.answers:
        name, path = spec.split('=', 1)
        rows = F.read_jsonl(path)
        assert {r['id'] for r in rows} == set(prompts), f'{name}: ids differ from the prompts'
        for sample in sorted({r['sample'] for r in rows}):
            sub = [r for r in rows if r['sample'] == sample]
            assert len(sub) == len(prompts), f'{name} sample {sample}: {len(sub)} answers'
            report.setdefault(name, {})[f'sample{sample}'], per_answer[f'{name}:sample{sample}'] = summarize(sub, prompts, analyzer, accept)
    (args.out / 'heldout-checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    (args.out / 'heldout-checks-per-answer.json').write_text(json.dumps(per_answer, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(f'{"system":<18}{"sample":<9}{"answers":>8}{"words":>8}{"ended":>8}{"constr.raw":>11}{"constr.norm":>12}{"flagged":>9}')
    for name, d in report.items():
        for s, v in d.items():
            cp = lambda x: 'n/a' if x is None else f'{x:.3f}'  # noqa: E731
            print(f'{name:<18}{s:<9}{v["answers"]:>8}{v["mean_words"]:>8.1f}{v["ended_share"]:>8.3f}{cp(v["constraint_pass_raw"]):>11}{cp(v["constraint_pass_normalized"]):>12}{v["flagged_share"]:>9.3f}')


if __name__ == '__main__':
    main()
