"""On-policy preference pairs for Turkish answer quality (preference-rl exp-004): no editing.

  python tr_dpo_onpolicy_pairs.py build --prompts P --answers A --flags F --out DIR [--band 0.85 1.15] [--max-per-prompt 2]

For one prompt the model gave several answers. chosen = an answer the detectors do not flag and that ended properly, rejected = a flagged
answer of the SAME prompt with a similar length (word ratio inside the band, so length is not the signal). Both come from the model itself,
so content errors are on both sides and the consistent difference is what the detectors measure: unknown or English words, broken
constraints, loops, English replies, cut-off answers. The held-out prompts never get here (the prompt pool excludes them). The pairs are
labelled `on_policy`; nothing was written or edited by hand.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tr_dpo_flags import read_jsonl, write_jsonl, visible, words  # noqa: E402

MIN_WORDS = 5


def reasons(f):
    out = []
    for key in ('unfinished', 'empty', 'english_reply', 'loop'):
        if f[key]:
            out.append(key)
    if f['constraint']:
        out.append('constraint')
    if f['unknown_words']:
        out.append('unknown_words')
    if f['english_words']:
        out.append('english_words')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['build'])
    ap.add_argument('--prompts', type=Path, required=True)
    ap.add_argument('--answers', type=Path, required=True)
    ap.add_argument('--flags', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--band', type=float, nargs=2, default=(0.85, 1.15), metavar=('LOW', 'HIGH'), help='chosen/rejected word ratio')
    ap.add_argument('--max-per-prompt', type=int, default=2)
    args = ap.parse_args()

    prompts = {r['id']: r for r in read_jsonl(args.prompts)}
    flags = {(r['id'], r['sample']): r for r in read_jsonl(args.flags)}
    by_prompt = {}
    for a in read_jsonl(args.answers):
        f = flags[(a['id'], a['sample'])]
        text = visible(a['raw_output'])
        by_prompt.setdefault(a['id'], []).append(dict(sample=a['sample'], text=text, words=len(words(text)), flags=f, finished=a['finish_reason'] == 'eos'))
    pairs, stats = [], Counter()
    for pid, cands in sorted(by_prompt.items()):
        stats['prompts'] += 1
        clean = [c for c in cands if c['flags']['severity'] == 0 and c['finished'] and c['words'] >= MIN_WORDS]
        bad = [c for c in cands if c['flags']['severity'] > 0 and c['words'] >= MIN_WORDS]
        if not clean:
            stats['no_clean_answer'] += 1
            continue
        if not bad:
            stats['no_flagged_answer'] += 1
            continue
        combos = []
        for c in clean:
            for b in bad:
                ratio = c['words'] / b['words']
                if args.band[0] <= ratio <= args.band[1] and c['text'].strip() != b['text'].strip():
                    combos.append((abs(math.log(ratio)), c['sample'], b['sample'], c, b, ratio))
        if not combos:
            stats['no_length_matched_pair'] += 1
            continue
        combos.sort(key=lambda t: t[:3])
        used_c, used_b, taken = set(), set(), 0
        for _, _, _, c, b, ratio in combos:
            if c['sample'] in used_c or b['sample'] in used_b:
                continue
            used_c.add(c['sample'])
            used_b.add(b['sample'])
            p = prompts[pid]
            pairs.append(dict(id=f"{pid}#{c['sample']}-{b['sample']}", kind=p['kind'], source=p['source'],
                              prompt=[dict(role='user', content=p['prompt'])],
                              chosen=[dict(role='assistant', content=c['text'])], rejected=[dict(role='assistant', content=b['text'])],
                              chat_template_kwargs=dict(enable_thinking=False), rejected_reasons=reasons(b['flags']),
                              rejected_unknown=b['flags']['unknown_words'], rejected_finished=b['finished'], label='on_policy',
                              words_chosen=c['words'], words_rejected=b['words'], length_ratio=round(ratio, 3), lane='turkish'))
            taken += 1
            if taken == args.max_per_prompt:
                break
        stats['prompts_with_pairs'] += 1
    args.out.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out / 'pairs-tr-dpo4.jsonl', pairs)
    n = max(1, len(pairs))
    summary = dict(pairs=len(pairs), **stats,
                   rejected_reasons=dict(Counter(r for p in pairs for r in p['rejected_reasons'])),
                   rejected_only_reason=dict(Counter(p['rejected_reasons'][0] for p in pairs if len(p['rejected_reasons']) == 1)),
                   by_kind=dict(Counter(p['kind'] for p in pairs)),
                   mean_words_chosen=round(sum(p['words_chosen'] for p in pairs) / n, 1), mean_words_rejected=round(sum(p['words_rejected'] for p in pairs) / n, 1),
                   mean_length_ratio=round(sum(p['length_ratio'] for p in pairs) / n, 3), rejected_unfinished=sum(not p['rejected_finished'] for p in pairs),
                   pairs_sha256=hashlib.sha256((args.out / 'pairs-tr-dpo4.jsonl').read_bytes()).hexdigest())
    (args.out / 'pairs-summary.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
