"""Score the Turkish writing probe: constraints, unknown-word rate (Zeyrek), length, EOS; build a blind review sheet.

  score: python score_lfm3_writing_probe.py score --run-dir RUN [--run-dir ...]      (needs zeyrek for the word rate)
  sheet: python score_lfm3_writing_probe.py sheet --run-dir A --run-dir B ... --out DIR   (shuffled, labels hidden, key apart)
Human Turkish text sits near 1.4% unknown tokens with this analyzer (Belebele Turkish passages), so rates are read against it.
"""
import argparse
import json
from pathlib import Path
import random
import re
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lfm3_eval_v2_scoring as scoring  # noqa: E402

BASE = Path(__file__).resolve().parents[2] / 'experiments/turkish-capability/lfm3-1.7b'
PROMPTS = BASE / 'eval-v2/writing-prompts-tr.jsonl'
BULLET = re.compile(r'^\s*(?:[-*•]|\d+[.)])\s+', re.M)


def visible(raw):
    return scoring.split_thinking(raw, False)[0]


def count_sentences(text):
    text = re.sub(r'\d+[.,]\d+', 'N', text)
    return len([s for s in re.split(r'(?<=[.!?…])\s+', text.strip()) if re.search(r'\w', s)])


def check(text, spec):
    if not spec:
        return None
    ok = True
    if 'max_words' in spec:
        ok &= len(text.split()) <= spec['max_words']
    if 'exact_sentences' in spec:
        ok &= count_sentences(text) == spec['exact_sentences']
    if 'bullets' in spec:
        ok &= len(BULLET.findall(text)) == spec['bullets']
    for word in spec.get('must_include', []):
        ok &= word.lower() in text.lower()
    return ok


def load(run_dir):
    prompts = {r['id']: r for r in map(json.loads, PROMPTS.read_text(encoding='utf-8').splitlines())}
    answers = [json.loads(x) for x in (run_dir / 'answers.jsonl').read_text(encoding='utf-8').splitlines()]
    return prompts, answers


def cmd_score(args):
    from turkish_nonword_rate import Analyzer, tokens
    analyzer = Analyzer()
    for run_dir in args.run_dir:
        prompts, answers = load(run_dir)
        checks, words, lengths, caps, eos_missing = [], [], [], 0, 0
        for a in answers:
            text = visible(a['raw_output'])
            c = check(text, prompts[a['id']]['check'])
            if c is not None:
                checks.append(c)
            words.extend(tokens(text))
            lengths.append(len(text.split()))
            caps += a['hit_max_new_tokens']
            eos_missing += a['finish_reason'] != 'eos'
        rate = analyzer.rate(words)
        summary = dict(run=run_dir.name, answers=len(answers), constraint_pass=round(sum(checks) / len(checks), 3),
                       constraint_n=len(checks), unknown_token_rate=rate['token_rate'], english_token_rate=rate['english_token_rate'],
                       candidate_token_rate=rate['candidate_token_rate'], unknown_type_rate=rate['type_rate'],
                       top_unknown=rate['top_candidates'], mean_words=round(statistics.mean(lengths), 1),
                       cap_rate=round(caps / len(answers), 3), no_eos_rate=round(eos_missing / len(answers), 3))
        (run_dir / 'writing-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print(json.dumps({k: v for k, v in summary.items() if k != 'top_unknown'}, ensure_ascii=False))
        print('  top non-English unknown:', [w for w, _ in summary['top_unknown']])


def cmd_sheet(args):
    rng = random.Random(3407)
    runs = {d.name: load(d) for d in args.run_dir}
    prompts = next(iter(runs.values()))[0]
    args.out.mkdir(parents=True, exist_ok=True)
    key, parts = {}, ['# Turkish writing probe: blind review\n',
                      'For each prompt rate every answer 1-5 (1 = unusable, 3 = understandable but clearly non-native, 5 = natural). '
                      'Also mark any invented or wrong words you notice.\n']
    for pid, row in prompts.items():
        labels = [chr(65 + i) for i in range(len(runs))]
        names = list(runs)
        rng.shuffle(names)
        key[pid] = dict(zip(labels, names))
        parts.append(f'\n---\n\n## {pid} ({row["category"]})\n\n**Prompt:** {row["prompt"]}\n')
        for label, name in zip(labels, names):
            a = next(x for x in runs[name][1] if x['id'] == pid)
            parts.append(f'\n### {label}\n\n{visible(a["raw_output"]).strip()}\n\nRating (1-5): ____   Invented words: ____\n')
    (args.out / 'review-sheet.md').write_text('\n'.join(parts), encoding='utf-8', newline='\n')
    (args.out / 'review-key.json').write_text(json.dumps(key, indent=1), encoding='utf-8')
    print('wrote', args.out / 'review-sheet.md', 'and key for', len(key), 'prompts')


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('score')
    p.add_argument('--run-dir', type=Path, action='append', required=True)
    p.set_defaults(func=cmd_score)
    p = sub.add_parser('sheet')
    p.add_argument('--run-dir', type=Path, action='append', required=True)
    p.add_argument('--out', type=Path, required=True)
    p.set_defaults(func=cmd_sheet)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
