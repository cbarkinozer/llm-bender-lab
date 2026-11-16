"""Export submitted blind rankings without changing annotations; decode locally."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import itertools
import json
import os
from pathlib import Path
import hashlib
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
OUT = BASE / 'pilot80-runtime-local/argilla-blind-review-simple-v01'


def main():
    load_dotenv(ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env')
    receipt = json.loads((OUT / 'receipt.json').read_text(encoding='utf-8'))
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900').rstrip('/')
    response = requests.get(url + '/api/v1/datasets/' + receipt['dataset_id'] + '/records',
        params={'limit': 100, 'include': 'responses'},
        headers={'X-Argilla-Api-Key': os.getenv('ARGILLA_API_KEY', 'argilla.apikey')}, timeout=30)
    response.raise_for_status()
    data = response.json()
    keypath = OUT / 'PRIVATE-model-key.json'
    keys = {r['record_id']: r for r in json.loads(keypath.read_text(encoding='utf-8'))['records']}
    assert data['total'] == len(data['items']) == len(keys) == 20
    snapshot = OUT / ('owner-responses-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json')
    snapshot.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    counts = defaultdict(Counter)
    rows = []
    for record in data['items']:
        mapping = keys[record.get('external_id') or record['id']]
        submitted = [r for r in record.get('responses', []) if r['status'] == 'submitted']
        assert len(submitted) <= 1, 'Multiple reviewers require explicit adjudication'
        for r in submitted:
            ranks = {mapping['models'][v['value']]: v['rank'] for v in r['values']['ranking']['value']}
            assert set(ranks) == set(mapping['models'].values())
            rows.append(dict(holdout_id=mapping['holdout_id'], response_id=r['id'],
                             ranks=ranks, notes=r['values']['notes']['value']))
            for a, b in itertools.combinations(sorted(ranks), 2):
                counts[a + ' vs ' + b]['win' if ranks[a] < ranks[b] else 'loss' if ranks[a] > ranks[b] else 'tie'] += 1
    result = dict(exported_at_utc=datetime.now(timezone.utc).isoformat(), submitted_records=len(rows),
        total_records=20, rank_1_is_best=True, pairwise_as_entered_first_model=dict(counts),
        snapshot=snapshot.name, snapshot_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),
        private_key_sha256=hashlib.sha256(keypath.read_bytes()).hexdigest(), records=rows,
        caution='Preserve note/rank conflicts; no automatic inversion, correctness scores or population claims.')
    (OUT / 'decoded-owner-review.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['submitted_records', 'pairwise_as_entered_first_model', 'snapshot_sha256']}, indent=2))


if __name__ == '__main__':
    main()
