"""Paired per-task bootstrap intervals; no pooled accuracy or significance claim."""
import argparse
import json
from pathlib import Path
import random
import statistics

METRICS = {'gecturk': ['exact_match'], 'tquad': ['exact_match', 'f1'],
    'xquad_tr': ['exact_match', 'f1'], 'wmt_en_tr': ['sentence_chrf'],
    'mlsum_tr': ['rouge1', 'rouge2', 'rougeL']}


def paired(values, rng, repeats=5000):
    n = len(values)
    boots = sorted(sum(rng.choice(values) for _ in range(n)) / n for _ in range(repeats))
    return dict(n=n, mean_F_minus_base=statistics.mean(values),
        bootstrap_percentile_95_interval=[boots[int(.025 * repeats)], boots[int(.975 * repeats)]],
        wins=sum(v > 0 for v in values), losses=sum(v < 0 for v in values), ties=sum(v == 0 for v in values))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-root', type=Path, required=True)
    args = parser.parse_args()
    arms = {arm: [json.loads(s) for s in (args.results_root / arm / 'scored-samples.jsonl').read_text(encoding='utf-8').splitlines()]
        for arm in ('base', 'F')}
    assert len(arms['base']) == len(arms['F']) == 500
    assert [r['id'] for r in arms['base']] == [r['id'] for r in arms['F']]
    results = {}
    for task, metrics in METRICS.items():
        pairs = [(a, b) for a, b in zip(arms['base'], arms['F']) if a['task'] == task]
        assert len(pairs) == len({a['source_group_sha256'] for a, _ in pairs}) == 100
        results[task] = {metric: paired([b[metric] - a[metric] for a, b in pairs],
            random.Random('paired-500-3407-' + task + '-' + metric)) for metric in metrics}
    report = dict(method='5000 paired source-item bootstrap resamples, percentile95, seed3407', results=results,
        translation_interval='Mean SENTENCE chrF difference, not corpus chrF or corpus BLEU.',
        limitations=['Exploratory intervals, no multiple-comparison correction or formal superiority claim.',
            'Reference overlap is not semantic correctness; source-group sampling is not full CETVEL representativeness.'])
    (args.results_root / 'paired-analysis.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
