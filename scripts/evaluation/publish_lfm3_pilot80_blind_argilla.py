"""Publish the frozen holdout comparison without identities or suggested grades."""
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import uuid

import argilla as rg
from dotenv import load_dotenv
import requests

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
RUNTIME = BASE / 'pilot80-runtime-local'
OUT = RUNTIME / 'argilla-blind-review-simple-v01'
NAME = 'turkish-pilot80-blind-holdout20-simple-v01'
MODELS = ['cpt', 'exp-005-sft-lr1e4', 'exp-006-sft-lr2e4']
LABELS = ['A', 'B', 'C']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def prepare():
    packet = [json.loads(line) for line in (RUNTIME / 'holdout20.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(packet) == 20 and len({r['id'] for r in packet}) == 20
    outputs = {}
    source_hashes = {'holdout20.jsonl': digest(RUNTIME / 'holdout20.jsonl')}
    for model in MODELS:
        path = RUNTIME / 'inference' / model / 'holdout20' / 'answers.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        assert len(rows) == 20
        outputs[model] = {r['id']: r for r in rows}
        assert set(outputs[model]) == {r['id'] for r in packet}
        source_hashes[model] = digest(path)
    rng = random.Random(34072026)
    # Three full permutation cycles plus two cyclic orders: 6 or 7 appearances
    # for each model in each position. Shuffle the assignments and prompt order.
    permutations = list(itertools.permutations(MODELS)) * 3
    permutations += [tuple(MODELS), tuple(MODELS[1:] + MODELS[:1])]
    rng.shuffle(permutations)
    rng.shuffle(packet)
    records, key = [], []
    for row, order in zip(packet, permutations):
        rid = str(uuid.uuid5(uuid.NAMESPACE_URL, NAME + ':' + row['id']))
        fields = {'prompt': '\n\n'.join(m['role'].upper() + ':\n' + m['content'] for m in row['messages'])}
        for label, model in zip(LABELS, order):
            fields['answer_' + label.lower()] = outputs[model][row['id']]['prediction']
        fields['reference'] = row['target']
        records.append({'id': rid, 'fields': fields})
        key.append({'record_id': rid, 'holdout_id': row['id'], 'models': dict(zip(LABELS, order))})
    assert all(6 <= sum(r['models'][label] == model for r in key) <= 7 for model in MODELS for label in LABELS)
    OUT.mkdir(parents=True, exist_ok=True)
    private = OUT / 'PRIVATE-model-key.json'
    payload = {'source_sha256': source_hashes, 'records': key}
    if private.exists():
        assert json.loads(private.read_text(encoding='utf-8')) == payload, 'Frozen private key differs'
    else:
        save(private, payload)
    save(OUT / 'anonymous-records.json', records)
    return records, source_hashes


def schema():
    questions = [
        rg.RankingQuestion(name='ranking', title='Order A / B / C from best to worst (ties allowed)', values=LABELS, required=True),
        rg.TextQuestion(name='notes', title='Your reasoning', description='Explain your ordering in your own words. Mention ties, all-bad answers or uncertainty here if relevant.', required=True),
    ]
    return rg.Settings(
        guidelines=(
            'Order A/B/C from best to worst, then explain your reasoning in the text box. '
            'Ties are allowed; say in your reasoning if all answers are bad or you are uncertain. '
            'Judge the complete answer against the prompt. Do not prefer length for its own sake. '
            'The reference is an anchor and may be imperfect. '
            'A/B/C identities change per prompt; no model names or automatic grades are shown. '
            'Submit each record to save. These20 prompts and answers remain evaluation-only.'
        ),
        fields=[rg.TextField(name='prompt', title='Complete prompt', use_markdown=False)]
        + [rg.TextField(name='answer_' + c.lower(), title='Answer ' + c, use_markdown=False) for c in LABELS]
        + [rg.TextField(name='reference', title='Reference anchor (may be imperfect)', use_markdown=False)],
        questions=questions,
        allow_extra_metadata=False,
    )


def main():
    records, hashes = prepare()
    env = ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env'
    load_dotenv(env)
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900').rstrip('/')
    key = os.getenv('ARGILLA_API_KEY', 'argilla.apikey')
    workspace = os.getenv('ARGILLA_WORKSPACE', 'sft-review')
    client = rg.Argilla(api_url=url, api_key=key)
    assert client.workspaces(name=workspace) is not None, 'Existing review workspace missing'
    dataset = client.datasets(name=NAME, workspace=workspace)
    if dataset is None:
        dataset = rg.Dataset(name=NAME, workspace=workspace, settings=schema(), client=client).create()
    expected = {r['id']: r['fields'] for r in records}
    current = {str(r.id): r for r in dataset.records}
    assert set(current) <= set(expected), 'Unexpected existing records; refusing to overwrite'
    for rid, record in current.items():
        assert record.to_dict()['fields'] == expected[rid], 'Existing display differs; refusing to overwrite'
    pending = [rg.Record(id=r['id'], fields=r['fields']) for r in records if r['id'] not in current]
    if pending:
        dataset.records.log(pending, batch_size=20)
    response = requests.get(url + f'/api/v1/datasets/{dataset.id}/records', params={'limit': 100, 'include': 'responses'}, headers={'X-Argilla-Api-Key': key}, timeout=30)
    response.raise_for_status()
    result = response.json()
    assert result['total'] == 20
    for row in result['items']:
        rid = str(row.get('external_id') or row['id'])
        assert row['fields'] == expected[rid], 'Display roundtrip differs'
        assert not row.get('suggestions') and not row.get('metadata'), 'Nonblind annotations uploaded'
    receipt = {'dataset_id': str(dataset.id), 'name': NAME, 'workspace': workspace, 'records': 20,
               'url': url + f'/dataset/{dataset.id}/annotation-mode', 'added': len(pending),
               'per_record_randomization': True, 'balanced_positions': True,
               'model_identities_uploaded': False, 'automatic_scores_uploaded': False,
               'full_outputs_roundtrip_verified': True, 'source_sha256': hashes,
               'submitted': sum(any(r['status'] == 'submitted' for r in row.get('responses', [])) for row in result['items'])}
    save(OUT / 'receipt.json', receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
