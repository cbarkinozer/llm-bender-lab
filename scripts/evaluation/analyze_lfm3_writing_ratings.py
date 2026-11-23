"""Unblind a rated writing-probe review sheet and report per-model and paired scores (CPU, local).

  python analyze_lfm3_writing_ratings.py --folder REVIEW_DIR --blank BLANK_SHEET.md [--out OUT.json]
REVIEW_DIR holds review-sheet.md (rated), review-ratings.json (rater's scores) and review-key.json (label -> model).
Checks: the JSON scores equal the footer lines of the sheet, and the sheet equals the unrated BLANK_SHEET once the footer
lines are blanked (so only rating lines changed). Naturalness 1-5; task yes=1, partly=.5, no=0; flagged words are the
';'-separated entries. Paired differences resample prompts (10,000 draws, seed 3407).
"""
import argparse
from collections import defaultdict
import itertools
import json
from pathlib import Path
import random
import re
import statistics

FOOTER = re.compile(r'^Naturalness \(1-5\):.*$')
TASK = {'yes': 1.0, 'partly': 0.5, 'no': 0.0}


def read_lines(path):
    return Path(path).read_bytes().decode('utf-8').replace('\r\n', '\n').split('\n')


def footers(lines):
    out = []
    for line in lines:
        m = re.match(r'^Naturalness \(1-5\):\s*(\S+)\s+Task \(yes/partly/no\):\s*(\S+)\s+Invented or wrong words:\s*(.*)$', line)
        if m:
            out.append((int(m.group(1)), m.group(2), m.group(3).strip()))
    return out


def blanked(lines):
    return [FOOTER.sub('<footer>', line) for line in lines]


def boot(diffs, n=10000, seed=3407):
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(diffs, k=len(diffs))) for _ in range(n))
    return round(means[int(.025 * n)], 3), round(means[int(.975 * n)], 3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--blank', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    ratings = json.loads((args.folder / 'review-ratings.json').read_text(encoding='utf-8'))['ratings']
    key = json.loads((args.folder / 'review-key.json').read_text(encoding='utf-8'))
    sheet = read_lines(args.folder / 'review-sheet.md')
    blank = read_lines(args.blank)
    checks = {}
    checks['only_footer_lines_changed'] = blanked(sheet) == blanked(blank)
    sheet_footers = footers(sheet)
    checks['footer_count'] = len(sheet_footers)
    checks['json_matches_sheet'] = (len(sheet_footers) == len(ratings) and all(
        (r['naturalness'], r['task'], r['words'].strip()) == f for r, f in zip(ratings, sheet_footers)))
    checks['no_blank_ratings'] = all(1 <= r['naturalness'] <= 5 and r['task'] in TASK for r in ratings)
    if not all(v for k, v in checks.items() if k != 'footer_count'):
        print(json.dumps(checks, indent=1))
        raise SystemExit('integrity check failed')
    by_model = defaultdict(dict)
    for r in ratings:
        model = key[r['id']][r['label']]
        words = [w for w in (x.strip() for x in r['words'].split(';')) if w]
        by_model[model][r['id']] = dict(nat=r['naturalness'], task=TASK[r['task']], yes=r['task'] == 'yes',
                                        flags=len(words), no_turkish=r['naturalness'] == 1 and r['task'] == 'no')
    result = dict(integrity=checks, models={}, paired={})
    for model, rows in sorted(by_model.items()):
        v = list(rows.values())
        result['models'][model] = dict(
            answers=len(v), mean_naturalness=round(statistics.fmean(x['nat'] for x in v), 3),
            share_natural_4plus=round(sum(x['nat'] >= 4 for x in v) / len(v), 3),
            share_nat_1_or_2=round(sum(x['nat'] <= 2 for x in v) / len(v), 3),
            task_score=round(statistics.fmean(x['task'] for x in v), 3), task_yes=round(sum(x['yes'] for x in v) / len(v), 3),
            flagged_words_per_answer=round(statistics.fmean(x['flags'] for x in v), 2))
    for a, b in itertools.permutations(sorted(by_model), 2):
        if a > b:
            continue
        ids = sorted(set(by_model[a]) & set(by_model[b]))
        entry = {'prompts': len(ids)}
        for metric in ('nat', 'task', 'flags'):
            d = [by_model[a][i][metric] - by_model[b][i][metric] for i in ids]
            lo, hi = boot(d)
            entry[metric] = dict(delta=round(statistics.fmean(d), 3), ci=[lo, hi])
        entry['prompts_a_more_natural'] = sum(by_model[a][i]['nat'] > by_model[b][i]['nat'] for i in ids)
        entry['prompts_b_more_natural'] = sum(by_model[a][i]['nat'] < by_model[b][i]['nat'] for i in ids)
        entry['prompts_tied'] = sum(by_model[a][i]['nat'] == by_model[b][i]['nat'] for i in ids)
        result['paired'][f'{a} - {b}'] = entry
    print(json.dumps(result, indent=1))
    if args.out:
        args.out.write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
