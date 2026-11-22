"""Unblind and summarize a rated Turkish writing-probe sheet (run after review-ratings.json exists).

  python summarize_lfm3_writing_review.py --review-dir .../writing-review --runs-dir .../results-local/writing-runs
Checks coverage (40 prompts x 4 labels, ratings 1-5), that the answer text in review-sheet.md still equals the generated
answers, then opens review-key.json and reports per-model ratings with prompt-level paired bootstrap differences.
The rater's identity and blinding level are read from review-ratings.json and printed, never assumed.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import random
import re
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lfm3_eval_v2_scoring as scoring  # noqa: E402

PROMPTS = Path(__file__).resolve().parents[2] / 'experiments/turkish-capability/lfm3-1.7b/eval-v2/writing-prompts-tr.jsonl'
MODELS = ['base', 'cpt', 'selfdistill-a', 'selfdistill-b-cpt']
PAIRS = [('selfdistill-b-cpt', 'base'), ('selfdistill-a', 'base'), ('selfdistill-b-cpt', 'selfdistill-a'), ('cpt', 'base')]


def sheet_answers(text):
    """{(prompt_id, label): answer_text} from the sheet; the answer ends at the Rating line."""
    out = {}
    for section in re.split(r'^## (?=wr-tr-)', text, flags=re.M)[1:]:
        pid = section.split(' ', 1)[0]
        for label, body in re.findall(r'^### ([ABCD])\n\n(.*?)\n\nRating \(1-5\):', section, flags=re.M | re.S):
            out[(pid, label)] = body.strip()
    return out


def boot(diffs, reps=4000, seed=3407):
    rng = random.Random(seed)
    means = sorted(statistics.mean(diffs[rng.randrange(len(diffs))] for _ in diffs) for _ in range(reps))
    return round(statistics.mean(diffs), 3), round(means[int(.025 * reps)], 3), round(means[int(.975 * reps) - 1], 3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--review-dir', type=Path, required=True)
    parser.add_argument('--runs-dir', type=Path, required=True)
    args = parser.parse_args()
    review = json.loads((args.review_dir / 'review-ratings.json').read_text(encoding='utf-8'))
    ratings = review['ratings']
    keys = {(r['prompt_id'], r['answer']) for r in ratings}
    assert len(ratings) == 160 and len(keys) == 160, 'expected 160 distinct (prompt, label) ratings'
    assert all(r['rating'] in (1, 2, 3, 4, 5) for r in ratings), 'rating outside 1-5'
    assert {p for p, _ in keys} == {f'wr-tr-{i:02d}' for i in range(1, 41)}, 'prompt coverage'
    print('rater:', review['reviewer'], '|', review['assessment_type'], '| key opened by rater:', review['review_key_opened'])

    key = json.loads((args.review_dir / 'review-key.json').read_text(encoding='utf-8'))
    source = {}
    for model in MODELS:
        for line in (args.runs_dir / model / 'answers.jsonl').read_text(encoding='utf-8').splitlines():
            a = json.loads(line)
            source[(model, a['id'])] = scoring.split_thinking(a['raw_output'], False)[0].strip()
    shown = sheet_answers((args.review_dir / 'review-sheet.md').read_text(encoding='utf-8'))
    assert len(shown) == 160, f'parsed {len(shown)} answer blocks'
    changed = [k for k, text in shown.items() if text != source[(key[k[0]][k[1]], k[0])]]
    print('answer blocks differing from the generated answers:', len(changed), changed[:5])

    per_model = defaultdict(dict)
    notes = defaultdict(list)
    for r in ratings:
        model = key[r['prompt_id']][r['answer']]
        per_model[model][r['prompt_id']] = r['rating']
        if not r['lexical_notes'].lower().startswith('none identified'):
            notes[model].append(r['prompt_id'])
    category = {json.loads(x)['id']: json.loads(x)['category']
                for x in PROMPTS.read_text(encoding='utf-8').splitlines()}
    summary = dict(rater=review['reviewer'], assessment_type=review['assessment_type'], models={}, paired={})
    for model in MODELS:
        vals = list(per_model[model].values())
        by_cat = defaultdict(list)
        for pid, v in per_model[model].items():
            by_cat[category[pid]].append(v)
        summary['models'][model] = dict(
            mean=round(statistics.mean(vals), 2), distribution=dict(sorted(Counter(vals).items())),
            share_1_2=round(sum(v <= 2 for v in vals) / len(vals), 3), share_4_5=round(sum(v >= 4 for v in vals) / len(vals), 3),
            lexical_flag_answers=len(notes[model]), by_category={c: round(statistics.mean(v), 2) for c, v in sorted(by_cat.items())})
        print(model, json.dumps(summary['models'][model], ensure_ascii=False))
    for a, b in PAIRS:
        diffs = [per_model[a][p] - per_model[b][p] for p in per_model[a]]
        summary['paired'][f'{a}-minus-{b}'] = dict(zip(('mean', 'lo', 'hi'), boot(diffs)))
        print(f'{a} minus {b}:', summary['paired'][f'{a}-minus-{b}'])
    (args.review_dir / 'review-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
