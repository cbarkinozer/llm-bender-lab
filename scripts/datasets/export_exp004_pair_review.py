"""Export the owner's labels of the exp-004 pair spot-check from local Argilla and print the rates that decide whether to train.

  python export_exp004_pair_review.py [--api-url URL] [--workspace NAME] [--name NAME]

Writes results-local/pair-review-labels.jsonl (id, reason, labels, notes). Only submitted responses count.
"""
import argparse
import json
import os
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / 'experiments/preference-rl/lfm3-1.7b/exp-004-dpo-onpolicy-turkish/results-local'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--api-url', default=os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900'))
    ap.add_argument('--workspace', default=os.getenv('ARGILLA_WORKSPACE', 'sft-review'))
    ap.add_argument('--name', default='exp004-dpo-pairs-spotcheck-30-v2')
    ap.add_argument('--drafts', action='store_true', help='also read unsubmitted (draft) answers')
    args = ap.parse_args()
    import argilla as rg
    client = rg.Argilla(api_url=args.api_url, api_key=os.getenv('ARGILLA_API_KEY', 'argilla.apikey'))
    dataset = client.datasets(name=args.name, workspace=args.workspace)
    if dataset is None:
        raise ValueError('dataset not found')
    rows = []
    for record in dataset.records(with_responses=True):
        got = {}
        states = set()
        for response in record.responses:
            if args.drafts or str(getattr(response, 'status', 'submitted')).endswith('submitted'):
                got[response.question_name] = response.value
                states.add(str(response.status).split('.')[-1])
        rows.append(dict(id=record.id, reason=(record.metadata or {}).get('reason'), status=sorted(states), **{k: got.get(k) for k in ('chosen_quality', 'rejected_problem', 'pair_usable', 'corrected_chosen', 'notes')}))
    out = EXP / 'pair-review-labels.jsonl'
    out.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n', encoding='utf-8', newline='\n')
    done = [r for r in rows if r['pair_usable']]
    print(f'{len(done)} of {len(rows)} pairs labelled -> {out}')
    for key in ('chosen_quality', 'rejected_problem', 'pair_usable'):
        print(key, dict(Counter(r[key] for r in done)))
    by_reason = {}
    for r in done:
        d = by_reason.setdefault(r['reason'], Counter())
        d[r['pair_usable']] += 1
    print('usable by reason', {k: dict(v) for k, v in by_reason.items()})


if __name__ == '__main__':
    main()
