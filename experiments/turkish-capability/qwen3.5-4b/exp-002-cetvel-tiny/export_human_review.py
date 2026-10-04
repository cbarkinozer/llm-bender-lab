"""Read-only export of submitted human grades; verify raw answers and blind map."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def frozen(path, value):
    blob = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    if path.exists():
        assert path.read_bytes() == blob, f'Preserve existing snapshot: {path}'
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
    return hashlib.sha256(blob).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--experiment-dir', type=Path, default=HERE)
    parser.add_argument('--allow-partial', action='store_true')
    args = parser.parse_args()
    args.output_dir = args.output_dir or args.experiment_dir / 'human-review-v1'
    config = read(args.experiment_dir / 'config.json')
    expected_count = config.get('human_review_count', 20)
    link = read(args.results_root / 'argilla-link.json')
    mapping_path = args.results_root / 'blind-human-mapping-v1.json'
    mapping = read(mapping_path)
    assert hashlib.sha256(mapping_path.read_bytes()).hexdigest() == link['mapping_sha256']
    ids = read(args.experiment_dir / config.get('human_review_ids_file', 'data-v1/human-review-20-ids.json'))
    assert set(ids) == set(mapping) and len(ids) == expected_count
    indexed = {}
    for arm in ('base', 'F'):
        folder = args.results_root / arm
        manifest = read(folder / 'manifest.json')
        assert hashlib.sha256((folder / 'answers.jsonl').read_bytes()).hexdigest() == manifest['answers_sha256']
        indexed[arm] = {r['id']: r for r in map(json.loads,
            (folder / 'answers.jsonl').read_text(encoding='utf-8').splitlines())}
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900')
    request = urllib.request.Request(f"{url}/api/v1/datasets/{link['id']}/records?limit=100&include=responses",
        headers={'X-Argilla-Api-Key': os.getenv('ARGILLA_API_KEY', 'argilla.apikey')})
    raw = json.load(urllib.request.urlopen(request, timeout=30))
    assert raw['total'] == len(raw['items']) == expected_count
    records = {r['external_id']: r for r in raw['items']}
    assert set(records) == set(ids)
    rows, pending = [], []
    for item_id in ids:
        record = records[item_id]
        base = indexed['base'][item_id]
        assert record['fields']['conversation'] == base['semantic_prompt']
        for position, arm in mapping[item_id].items():
            assert record['fields']['answer_' + position] == indexed[arm][item_id]['raw_output']
        if not record['responses'] or all(r['status'] != 'submitted' for r in record['responses']):
            pending.append(item_id)
            continue
        assert len(record['responses']) == 1 and record['responses'][0]['status'] == 'submitted', item_id
        response = record['responses'][0]
        values = response['values']
        best = values['best_output']['value']
        assert best in ('P', 'Q', 'tie', 'neither')
        grades = {arm: values[position + '_grade']['value'] for position, arm in mapping[item_id].items()}
        assert set(grades.values()) <= {'pass', 'partial', 'fail'}
        rows.append(dict(id=item_id, task=base['task'], grades=grades,
            preference=mapping[item_id].get(best, best), selected_position=best,
            notes=values.get('notes', {}).get('value', ''),
            response_id=response['id'], updated_at=response['updated_at']))
    assert not pending or args.allow_partial, pending
    def counts(group):
        return {arm: {g: sum(r['grades'][arm] == g for r in group)
            for g in ('pass', 'partial', 'fail')} for arm in ('base', 'F')}
    snapshot_name = 'partial-human-review-v1-raw.json' if pending else 'completed-human-review-v1-raw.json'
    raw_hash = frozen(args.results_root / snapshot_name, raw)
    summary = dict(count=len(rows), expected_count=expected_count, pending_ids=pending,
        status='partial' if pending else 'completed', grades=counts(rows),
        preferences=dict(collections.Counter(r['preference'] for r in rows)),
        by_task={t: dict(grades=counts([r for r in rows if r['task'] == t]),
            preferences=dict(collections.Counter(r['preference'] for r in rows if r['task'] == t)))
            for t in sorted({r['task'] for r in rows})},
        ties_not_allocated=True, raw_snapshot_sha256=raw_hash,
        limitations=['One human reviewer, four random items per task, diagnostic pilot.' if expected_count == 20
            else f'One human reviewer, {expected_count // 5} random items per task, diagnostic generation subset.',
            'No separate numeric fluency/grammar scores; do not infer them from preference.'])
    frozen(args.output_dir / 'review.json', rows)
    frozen(args.output_dir / 'summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
