"""Preserve submitted free-text rankings/notes and decode the local blind key."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import uuid

from dotenv import load_dotenv
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'experiments/turkish-capability/lfm3-1.7b/pilot160-runtime-local/argilla-blind-dev20-v01'


def parse_ranking(value):
    assert isinstance(value, str), 'Ordering must be text'
    text = value.upper().strip().replace('→', '>')
    assert re.fullmatch(r'[A-E\s>,;=]+', text), 'Use A-E with >, spaces, commas or = for ties'
    text = re.sub(r'\s*=\s*', '=', text)
    groups = re.split(r'[>,;\s]+', text)
    ranks = {}
    for rank, group in enumerate(groups, 1):
        for letter in group.split('='):
            assert letter in 'ABCDE' and len(letter) == 1 and letter not in ranks, 'Missing/duplicate letter or malformed tie'
            ranks[letter] = rank
    assert set(ranks) == set('ABCDE'), 'Use every letter exactly once'
    return ranks


def main():
    load_dotenv(ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env')
    receipt = json.loads((OUT / 'receipt.json').read_text(encoding='utf-8'))
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900').rstrip('/')
    response = requests.get(url + '/api/v1/datasets/' + receipt['dataset_id'] + '/records',
        params={'limit': 100, 'include': 'responses'},
        headers={'X-Argilla-Api-Key': os.getenv('ARGILLA_API_KEY', 'argilla.apikey')}, timeout=30)
    response.raise_for_status()
    snapshot = response.json()
    keypath = OUT / 'PRIVATE-model-key.json'
    keys = {r['record_id']: r for r in json.loads(keypath.read_text(encoding='utf-8'))['records']}
    assert snapshot['total'] == len(snapshot['items']) == len(keys) == 20
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:6]
    path = OUT / ('owner-responses-' + stamp + '.json')
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    decoded, invalid = [], []
    counts = defaultdict(Counter)
    submitted = 0
    for record in snapshot['items']:
        mapping = keys[record['external_id']]
        answers = [r for r in record.get('responses', []) if r['status'] == 'submitted']
        assert len(answers) <= 1, 'Multiple reviewers require adjudication'
        for answer in answers:
            submitted += 1
            values = answer['values']
            raw = values.get('ranking', {}).get('value', '')
            notes = values.get('notes', {}).get('value', '')
            try:
                ranks = {mapping['models'][label]: rank for label, rank in parse_ranking(raw).items()}
            except AssertionError as error:
                invalid.append(dict(dev_id=mapping['dev_id'], response_id=answer['id'], raw_ranking=raw, notes=notes, issue=str(error)))
                continue  # Never guess missing positions or silently invert an ordering.
            decoded.append(dict(dev_id=mapping['dev_id'], response_id=answer['id'], raw_ranking=raw, ranks=ranks, notes=notes))
            for a, b in itertools.combinations(sorted(ranks), 2):
                counts[a + ' vs ' + b]['win' if ranks[a] < ranks[b] else 'loss' if ranks[a] > ranks[b] else 'tie'] += 1
    result = dict(submitted_records=submitted, valid_rankings=len(decoded), total_records=20,
        snapshot=path.name, snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        private_key_sha256=hashlib.sha256(keypath.read_bytes()).hexdigest(),
        pairwise_first_model=dict(counts), records=decoded, invalid_rankings=invalid,
        policy='Preserve notes and ordering verbatim. Dense ranks start at1; equal positions are ties. No correctness/pass scores inferred. These20 are development only.')
    (OUT / 'decoded-owner-review.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # Do not leak identities or interim preferences while the owner is still reviewing.
    print(json.dumps(dict(submitted_records=submitted, valid_rankings=len(decoded), invalid_rankings=len(invalid), total_records=20)))


if __name__ == '__main__':
    main()
