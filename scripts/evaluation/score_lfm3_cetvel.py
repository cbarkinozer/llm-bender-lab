"""Score complete or diagnostic LFM3 output with the historical CPU scorers."""
import argparse
from collections import Counter
import json
from pathlib import Path
from score_cetvel_generation import SCORERS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-dir', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.results_dir / 'manifest.json').read_text())
    rows = [json.loads(line) for line in (args.results_dir / 'answers.jsonl').read_text(encoding='utf-8').splitlines()]
    if manifest['status'] != 'completed' or len(rows) != manifest['expected_count']:
        raise ValueError('Incomplete run; preserve and diagnose before scoring as completed')
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate output IDs')
    results = {task: scorer(group) for task, scorer in SCORERS.items()
        if (group := [r for r in rows if r['task'] == task])}
    report = dict(status='scored', diagnostic=manifest['diagnostic'],
        questions_sha256=manifest['questions_sha256'], results=results,
        termination=dict(Counter(r['finish_reason'] for r in rows)),
        note='Reference-overlap metrics; no pooled accuracy. Incomplete generations retained, not dropped.')
    (args.results_dir / 'scores.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (args.results_dir / 'scored-samples.jsonl').write_text(
        ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
