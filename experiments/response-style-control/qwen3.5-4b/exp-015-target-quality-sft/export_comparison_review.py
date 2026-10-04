"""Read-only export of completed v3 review; partition future manual-review focus."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path

from import_comparison import MODELS, POSITIONS, balanced_mapping, load
from import_simple_comparison import fetch

DATASET_ID = 'ff9f4e4c-796b-4595-aa33-0229137b6258'


def save(path, value):
    content = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if path.exists():
        assert path.read_bytes() == content, f'Preserve prior review snapshot: {path}'
    else:
        path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def summarize(rows):
    def counts(selected):
        return {model: {grade: sum(r['grades'][model] == grade for r in selected)
                        for grade in ('pass', 'partial', 'fail')} for model in MODELS}
    all_pass = [r['id'] for r in rows if all(g == 'pass' for g in r['grades'].values())]
    focus = [r['id'] for r in rows if r['id'] not in all_pass]
    assert set(all_pass).isdisjoint(focus) and len(all_pass) + len(focus) == len(rows)
    return dict(
        count=len(rows), grades=counts(rows),
        by_group={group: counts([r for r in rows if r['split'] == group])
                  for group in sorted({r['split'] for r in rows})},
        by_category={category: counts([r for r in rows if r['category'] == category])
                     for category in sorted({r['category'] for r in rows})},
        without_me089=counts([r for r in rows if r['id'] != 'me-089']),
        preferences=dict(collections.Counter(r['best_model_or_tie_neither'] for r in rows)),
        unanimous_pass_ids=all_pass, next_manual_focus_ids=focus,
        exact_identical_unanimous_pass_ids=[r['id'] for r in rows
            if r['id'] in all_pass and r['all_outputs_identical']],
        ties_not_allocated=True,
        limitations=['One reviewer, one generation seed, development/diagnostic items.',
                     'Tie subsets retained in notes; not automatically inferred or allocated.',
                     'All-pass is a current observation, not permanent mastery.',
                     'Focus subset is selected after outcomes; not comparable to full32 scores.',
                     'No separate Turkish/style scores collected.'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    arms = load(args.results_root)
    baseline = arms['base'][1]
    mapping_path = args.results_root / 'blind-mapping-v1.json'
    mapping = json.loads(mapping_path.read_text(encoding='utf-8'))
    assert mapping == balanced_mapping([r['id'] for r in baseline])
    link = json.loads((args.results_root / 'argilla-simple-link.json').read_text())
    assert link['id'] == DATASET_ID
    assert hashlib.sha256(mapping_path.read_bytes()).hexdigest() == link['mapping_sha256']
    raw = fetch(os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900'),
                os.getenv('ARGILLA_API_KEY', 'argilla.apikey'), DATASET_ID)
    assert raw['total'] == len(raw['items']) == 32
    records = {r['external_id']: r for r in raw['items']}
    assert set(records) == set(mapping)
    indexed = {model: {r['id']: r for r in data} for model, (_, data) in arms.items()}
    rows = []
    for base in baseline:
        item_id = base['id']
        record = records[item_id]
        assert record['fields']['desired_answer'] == base['desired_answer']
        assert record['fields']['conversation'] == '\n\n'.join(
            m['role'] + ': ' + m['content'] for m in base['messages'])
        responses = record['responses']
        assert len(responses) == 1 and responses[0]['status'] == 'submitted', item_id
        response = responses[0]
        values = response['values']
        best = values['best_output']['value']
        assert best in (*POSITIONS, 'tie', 'neither')
        grades = {}
        answers = []
        for position, model in mapping[item_id].items():
            answer = indexed[model][item_id]['answer']
            assert record['fields']['answer_' + position] == answer
            answers.append(answer)
            grade = values[position + '_grade']['value']
            assert grade in ('pass', 'partial', 'fail')
            grades[model] = grade
        rows.append(dict(id=item_id, category=base['category'], split=base['split'],
                         messages=base['messages'], desired_answer=base['desired_answer'],
                         grades=grades, selected_position=best,
                         best_model_or_tie_neither=mapping[item_id].get(best, best),
                         notes=values.get('notes', {}).get('value', ''),
                         all_outputs_identical=len(set(answers)) == 1,
                         response_id=response['id'], updated_at=response['updated_at']))
    # Private raw API snapshot is external; the repo export omits user IDs.
    raw_hash = save(args.results_root / 'completed-review-v3-raw.json', raw)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize(rows)
    save(args.output_dir / 'per-item-review.json', rows)
    save(args.output_dir / 'summary.json', summary)
    save(args.output_dir / 'manual-review-partition.json', dict(
        source_dataset_id=DATASET_ID, selection='observed-all-four-pass-in-completed-v3',
        fixed_evaluation_ids=[r['id'] for r in rows],
        focused_manual_review_ids=summary['next_manual_focus_ids'],
        regression_watch_ids=summary['unanimous_pass_ids'],
        delete_from_validation=False, move_to_training=False,
        policy='Keep full32 inference; inspect changed outputs and failures on regression watch. '
               'Identical prompt/output/settings may reuse prior human grade with provenance; '
               'new generations are never automatically marked pass.'))
    save(args.output_dir / 'manifest.json', dict(
        dataset_id=DATASET_ID, count=32, all_submitted=True,
        raw_snapshot_sha256=raw_hash, mapping_sha256=link['mapping_sha256'],
        outputs_unchanged=True, api_mutations=False,
        files={name: hashlib.sha256((args.output_dir / name).read_bytes()).hexdigest()
               for name in ('per-item-review.json', 'summary.json', 'manual-review-partition.json')}))
    print(json.dumps(summary, ensure_ascii=True))


if __name__ == '__main__':
    main()
