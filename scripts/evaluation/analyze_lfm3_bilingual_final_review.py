"""Decode submitted task preferences with tie-corrected ranks and group bootstrap."""
import itertools
import json
from pathlib import Path
import random
import statistics

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'experiments/turkish-capability/lfm3-1.7b/final-eval-v01-local'
MODELS = ['base', 'turkish60', 'bilingual69']


def main():
    data = json.loads((RUN/'argilla/decoded-owner-review.json').read_text(encoding='utf-8'))
    reviews = data['reviews']
    assert data['valid_submitted'] == len(reviews) == 35 and not data['invalid']
    assert len({r['group_id'] for r in reviews}) == 35
    assert all(set(r['model_ranks']) == set(MODELS) for r in reviews)
    out = dict(snapshot_sha256=data['snapshot_sha256'], groups=35,
               bootstrap=dict(seed=3407, samples=10000, unit='task group', statistic='wins minus losses divided by all groups'),
               models={}, pairs={}, categories={})

    def preference_score(subset, model):
        return sum(sum(1 if r['model_ranks'][model] < r['model_ranks'][other]
                       else .5 if r['model_ranks'][model] == r['model_ranks'][other] else 0
                       for other in MODELS if other != model) for r in subset) / (2*len(subset))

    for model in MODELS:
        ranks = []
        top = 0
        for row in reviews:
            scores = row['model_ranks']
            ranks.append(1 + sum(v < scores[model] for v in scores.values())
                         + (sum(v == scores[model] for v in scores.values())-1)/2)
            top += scores[model] == min(scores.values())
        out['models'][model] = dict(mean_rank=statistics.mean(ranks),
            pairwise_score=preference_score(reviews, model), top_including_ties=top)
    for left, right in itertools.combinations(MODELS, 2):
        signs = [1 if r['model_ranks'][left] < r['model_ranks'][right]
                 else 0 if r['model_ranks'][left] == r['model_ranks'][right] else -1 for r in reviews]
        rng = random.Random(3407)
        boot = sorted(sum(rng.choices(signs, k=35))/35 for _ in range(10000))
        out['pairs'][left+' vs '+right] = dict(wins=signs.count(1), ties=signs.count(0), losses=signs.count(-1),
            net_win_rate=statistics.mean(signs), bootstrap_95_net_win_rate=[boot[249], boot[9749]])
    for category in ['ar', 'co', 'ne', 'sr', 'rw', 'ol']:
        subset = [r for r in reviews if r['group_id'].split('-')[1].startswith(category)]
        out['categories'][category] = dict(n=len(subset), pairwise_score={m:preference_score(subset, m) for m in MODELS})
    (RUN/'analysis/owner-preference-summary.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
