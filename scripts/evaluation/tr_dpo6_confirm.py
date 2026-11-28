"""exp-006 confirmatory analysis on the held-out prompts: rules 1-3 per seed, memorization check, blind-read sheet. No model judge.

  python tr_dpo6_confirm.py --prompts heldout.jsonl --parent parent.jsonl --pairs pairs.jsonl --seed-arm 101=dpo-s101.jsonl,sft-s101.jsonl \
      --seed-arm 102=dpo-s102.jsonl,sft-s102.jsonl --out-dir DIR [--boot 10000] [--blind-n 40] [--temperature 0.7]
Writes DIR/confirm-report.json, DIR/blind-sheet.md (what the readers see) and DIR/blind-key.json (which side is which; kept away from the readers).
The parent file may hold several temperatures; only --temperature rows are used (the arms were sampled at that temperature only).
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
import tr_dpo6_checks as C  # noqa: E402
import tr_dpo6_eval as E  # noqa: E402
import tr_dpo6_pairs as P  # noqa: E402


def grams(words, n):
    return [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]


def memorization(scored, train_grams, n):
    """Share of answer n-grams that occur verbatim in a training chosen answer; share of answers with at least one run of n+ words copied."""
    shares, hit = [], 0
    for cs in scored.values():
        for c in cs:
            g = grams(C.tr_words(c['text']), n)
            if not g:
                continue
            k = sum(x in train_grams for x in g)
            shares.append(k / len(g))
            hit += k > 0
    return dict(mean_ngram_share=statistics.mean(shares), answers_with_any=hit / len(shares), answers=len(shares))


def blind_sheet(prompts, dpo, ctrl, n, seed, out_dir):
    rng = random.Random(seed)
    ids = sorted(set(dpo) & set(ctrl))
    pick = rng.sample(ids, n)
    sheet, key = ['# exp-006 blind read\n', 'For each item, two answers to the same prompt (A and B). For each answer say: OK, or HACK with a short reason '
                  '(empty or skeleton answer, copied prompt text, gibberish, invented facts or numbers, constraint met only by degenerate text). '
                  'Then say which answer is better, or tie. You do not know which answer comes from which model.\n'], {}
    for i, pid in enumerate(pick, 1):
        a, b = dpo[pid][0], ctrl[pid][0]
        sides = [('dpo', a), ('control', b)]
        rng.shuffle(sides)
        key[f'{i:02d}'] = dict(prompt_id=pid, A=sides[0][0], B=sides[1][0])
        sheet.append(f"\n## Item {i:02d}\n\n**Prompt:** {prompts[pid]['prompt']}\n\n**Answer A:**\n\n{sides[0][1]['text']}\n\n**Answer B:**\n\n{sides[1][1]['text']}\n")
    (out_dir / 'blind-sheet.md').write_text(''.join(sheet), encoding='utf-8')
    (out_dir / 'blind-key.json').write_text(json.dumps(key, indent=1) + '\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prompts', type=Path, required=True)
    ap.add_argument('--parent', type=Path, required=True)
    ap.add_argument('--pairs', type=Path, required=True)
    ap.add_argument('--seed-arm', action='append', required=True, help='SEED=dpo.jsonl,control.jsonl')
    ap.add_argument('--out-dir', type=Path, required=True)
    ap.add_argument('--boot', type=int, default=10000)
    ap.add_argument('--bseed', type=int, default=11)
    ap.add_argument('--blind-n', type=int, default=40)
    ap.add_argument('--temperature', type=float, default=0.7)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    prompts = {r['id']: r for r in P.read_jsonl(args.prompts)}
    parent_rows = [r for r in P.read_jsonl(args.parent) if r.get('temperature') == args.temperature and r['id'] in prompts]
    parent = E.score_arm(prompts, parent_rows)
    parent_median = statistics.median(c['words'] for cs in parent.values() for c in cs)
    parent_rate = E.per_prompt_rates(parent)
    train_text = [r['chosen'] for r in P.read_jsonl(args.pairs)]
    n = 8
    train_grams = {g for t in train_text for g in grams(C.tr_words(t), n)}
    rep = dict(prompts=len(prompts), prompts_sha256=hashlib.sha256(args.prompts.read_bytes()).hexdigest(), temperature=args.temperature, boot=args.boot,
               parent=dict(pass_rate=statistics.mean(parent_rate.values()), **E.flags(prompts, parent, parent_median),
                           memorization=memorization(parent, train_grams, n)), seeds={})
    first = True
    for spec in args.seed_arm:
        seed, files = spec.split('=')
        dfile, cfile = files.split(',')
        res = {}
        scored = {}
        for name, f in (('dpo', dfile), ('control', cfile)):
            sc = E.score_arm(prompts, P.read_jsonl(f))
            scored[name] = sc
            rate = E.per_prompt_rates(sc)
            res[name] = dict(answers_file=f, answers_sha256=hashlib.sha256(Path(f).read_bytes()).hexdigest(), pass_rate=statistics.mean(rate.values()),
                             rates=rate, **E.flags(prompts, sc, parent_median), memorization=memorization(sc, train_grams, n))
        vs_ctrl = E.paired_bootstrap(res['dpo']['rates'], res['control']['rates'], args.boot, args.bseed)
        vs_par = E.paired_bootstrap(res['dpo']['rates'], parent_rate, args.boot, args.bseed)
        ctl_vs_par = E.paired_bootstrap(res['control']['rates'], parent_rate, args.boot, args.bseed)
        d, c = res['dpo'], res['control']
        ratio = d['mean_words'] / c['mean_words']
        rule3 = dict(words_ratio=ratio, words_ok=0.8 <= ratio <= 1.25, skeleton_share=d['skeleton_share'], skeleton_ok=d['skeleton_share'] <= 0.05,
                     source_copy_delta=(d['source_copy_rate'] or 0) - (c['source_copy_rate'] or 0), copy_ok=(d['source_copy_rate'] or 0) <= (c['source_copy_rate'] or 0) + 0.05,
                     invented_delta=(d['invented_share'] or 0) - (c['invented_share'] or 0), invented_ok=(d['invented_share'] or 0) <= (c['invented_share'] or 0) + 0.01)
        rule3['pass'] = all(rule3[k] for k in ('words_ok', 'skeleton_ok', 'copy_ok', 'invented_ok'))
        for arm in res.values():
            del arm['rates']
        rep['seeds'][seed] = dict(arms=res, dpo_minus_control=vs_ctrl, dpo_minus_parent=vs_par, control_minus_parent=ctl_vs_par,
                                  rule1=vs_ctrl['difference'] >= 0.03 and vs_ctrl['ci95'][0] > 0, rule2=vs_par['difference'] >= 0.03 and vs_par['ci95'][0] > 0, rule3=rule3)
        if first:
            dpo_c = {pid: cs for pid, cs in scored['dpo'].items()}
            ctl_c = {pid: cs for pid, cs in scored['control'].items()}
            blind_sheet(prompts, dpo_c, ctl_c, args.blind_n, 20261128, args.out_dir)
            first = False
    (args.out_dir / 'confirm-report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    for s, r in rep['seeds'].items():
        a = r['arms']
        print(f"seed {s}: parent {rep['parent']['pass_rate']*100:.1f}  control {a['control']['pass_rate']*100:.1f}  dpo {a['dpo']['pass_rate']*100:.1f} | "
              f"dpo-control {r['dpo_minus_control']['difference']*100:+.2f} {[round(x*100, 2) for x in r['dpo_minus_control']['ci95']]} rule1={r['rule1']} | "
              f"dpo-parent {r['dpo_minus_parent']['difference']*100:+.2f} rule2={r['rule2']} | rule3={r['rule3']['pass']} {r['rule3']}")


if __name__ == '__main__':
    main()
