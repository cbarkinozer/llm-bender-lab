"""Pairs for the skill-preserving lane (preference-rl exp-003): the model's verified answer against its own wrong answer.

  python tr_dpo_skill_pairs.py build --prompts P --samples S --verified V --out DIR [--cap 100] [--max-tokens 3000]

Input: output of generate_lfm3_sft_samples.py (k samples per prompt, from the model that is trained) and of verify_lfm3_sft_samples.py
(code needs --allow-exec on the pod). Output: `pairs-skills-dpo.jsonl` in the format of the example DPO code
({prompt, chosen, rejected, chat_template_kwargs[, tools]}), thinking kept in the assistant message like the SFT core pack.
Rules:
- chosen = a verified sample (checker passed, ended, thinking closed); rejected = a sample whose checker failed. Samples that were cut at the
  token budget or never closed their thinking are not used as rejected: TRL adds the end token to every assistant message, so a cut answer
  would look finished and teach the wrong lesson.
- Among the possible pairs of a prompt, the one with the most similar length (no length shortcut for DPO).
- The pair must fit: estimated prompt tokens + the longer answer <= --max-tokens (the example trains with max_length 3072).
- At most --cap pairs per category/language cell, chosen by a seeded hash so reruns give the same set.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/evaluation'))
import lfm3_eval_v2_scoring as scoring  # noqa: E402

CONTROL = ('<|im_end|>', '<|endoftext|>', '<|im_start|>')
NOT_REJECTED = ('no_eos', 'unclosed_thinking', 'not_executed')


def read_jsonl(path):
    with open(path, encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def split_sample(raw, thinking):
    answer, _ = scoring.split_thinking(raw, thinking)
    reasoning = None
    if thinking:
        text = raw
        for token in CONTROL:
            text = text.replace(token, '')
        reasoning = text.rsplit(scoring.THINK_CLOSE, 1)[0].strip()
    return reasoning, answer.strip()


def message(raw, thinking):
    reasoning, answer = split_sample(raw, thinking)
    out: dict = dict(role='assistant', content=answer)
    if thinking:
        out['thinking'] = reasoning
    return [out]


def rank(key):
    return hashlib.sha256(key.encode('utf-8')).hexdigest()


def mix(args):
    """Turkish repair pairs plus skill pairs in one file, in the format of the example DPO code (extra columns are for our own bookkeeping)."""
    turkish = [dict(p, lane='turkish') for p in read_jsonl(args.turkish)]
    skills = [dict(p, lane='skills') for p in read_jsonl(args.skills)]
    skills.sort(key=lambda p: rank('skill-mix:' + p['id']))
    seen, capped = Counter(), []
    for p in skills:  # per-cell cap in the hashed order, so one cell (Turkish math) cannot crowd out the guards
        cell = f"{p['category']}/{p['lang']}"
        if seen[cell] < args.cell_cap:
            seen[cell] += 1
            capped.append(p)
    keep = capped[:round(len(turkish) * args.skill_ratio)]
    rows = sorted(turkish + keep, key=lambda p: rank('mix-order:' + p['id']))
    for r in rows:
        assert set(('prompt', 'chosen', 'rejected', 'chat_template_kwargs')) <= set(r), r['id']
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'pairs-dpo.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + chr(10) for r in rows), encoding='utf-8', newline=chr(10))
    summary = dict(pairs=len(rows), turkish=len(turkish), skills=len(keep), skills_available=len(skills),
                   skills_by_cell=dict(Counter(f"{p['category']}/{p['lang']}" for p in keep)))
    (args.out / 'pairs-dpo.summary.json').write_text(json.dumps(summary, indent=1) + chr(10), encoding='utf-8')
    print(json.dumps(summary, indent=1))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cmd', choices=['build', 'mix'])
    parser.add_argument('--prompts', type=Path)
    parser.add_argument('--samples', type=Path)
    parser.add_argument('--verified', type=Path)
    parser.add_argument('--turkish', type=Path, help='mix: pairs-tr-dpo.jsonl (edited Turkish pairs)')
    parser.add_argument('--skills', type=Path, help='mix: pairs-skills-dpo.jsonl')
    parser.add_argument('--skill-ratio', type=float, default=1.0, help='mix: skill pairs per Turkish pair')
    parser.add_argument('--cell-cap', type=int, default=10**6, help='mix: at most this many skill pairs per category/language cell')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cap', type=int, default=100)
    parser.add_argument('--max-tokens', type=int, default=3000)
    args = parser.parse_args()
    if args.cmd == 'mix':
        return mix(args)
    assert args.prompts and args.samples and args.verified, 'build needs --prompts, --samples and --verified'

    prompts = {r['id']: r for r in read_jsonl(args.prompts)}
    samples = {r['id']: r for r in read_jsonl(args.samples)}
    verified = {r['id']: r for r in read_jsonl(args.verified)}
    cells, stats = defaultdict(list), Counter()
    for pid, prompt in prompts.items():
        if pid not in samples or pid not in verified:
            stats['not_sampled'] += 1
            continue
        flags, reasons, rows = verified[pid]['verified'], verified[pid]['reasons'], samples[pid]['samples']
        good = [i for i, ok in enumerate(flags) if ok]
        bad = [i for i, ok in enumerate(flags) if ok is False and reasons[i] not in NOT_REJECTED]
        stats['prompts_with_good'] += bool(good)
        stats['prompts_with_bad'] += bool(bad)
        if not good or not bad:
            continue
        chars = sum(len(m['content']) for m in prompt['messages']) + len(json.dumps(prompt.get('tools') or []))
        options = [(abs(rows[g]['tokens'] - rows[b]['tokens']), g, b) for g in good for b in bad
                   if max(rows[g]['tokens'], rows[b]['tokens']) + chars / 3 <= args.max_tokens]
        if not options:
            stats['too_long'] += 1
            continue
        _, g, b = min(options)
        thinking = bool(prompt['thinking'])
        pair = dict(id=pid, category=prompt['category'], lang=prompt['lang'], prompt=prompt['messages'],
                    chosen=message(rows[g]['raw_output'], thinking), rejected=message(rows[b]['raw_output'], thinking),
                    chat_template_kwargs=dict(enable_thinking=thinking), rejected_reason=reasons[b], label='own_verified',
                    chosen_tokens=rows[g]['tokens'], rejected_tokens=rows[b]['tokens'])
        if prompt.get('tools'):
            pair['tools'] = prompt['tools']
        cells[f"{prompt['category']}/{prompt['lang']}"].append(pair)
    pairs = []
    for cell, items in sorted(cells.items()):
        items.sort(key=lambda p: rank('skill-pair:' + p['id']))
        stats[f'cell {cell}: available'] = len(items)
        pairs += items[:args.cap]
    pairs.sort(key=lambda p: rank('skill-order:' + p['id']))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'pairs-skills-dpo.jsonl').write_text(''.join(json.dumps(p, ensure_ascii=False) + '\n' for p in pairs),
                                                     encoding='utf-8', newline='\n')
    summary = dict(pairs=len(pairs), by_cell=dict(Counter(f"{p['category']}/{p['lang']}" for p in pairs)),
                   rejected_reasons=dict(Counter(p['rejected_reason'] for p in pairs)), stats=dict(stats),
                   mean_tokens=dict(chosen=round(sum(p['chosen_tokens'] for p in pairs) / max(1, len(pairs))),
                                    rejected=round(sum(p['rejected_tokens'] for p in pairs) / max(1, len(pairs)))))
    (args.out / 'pairs-skills-dpo.summary.json').write_text(json.dumps(summary, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
