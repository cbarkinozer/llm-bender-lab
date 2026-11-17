"""Publish the four-way cross-lingual diagnostic without identities or suggested grades."""
import hashlib
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
RUNTIME = BASE / 'crosslingual-runtime-local'
OUT = RUNTIME / 'argilla-crosslingual-v01'
NAME = 'turkish-crosslingual-holdout-v01'
MODELS = ['base', 'cpt', 'base-sft', 'cpt-sft']
LABELS = ['A', 'B', 'C', 'D']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def prepare():
    packet = [json.loads(line) for line in (RUNTIME / 'combined-questions.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(packet) == 15 and len({r['id'] for r in packet}) == 15
    outputs = {}
    source_hashes = {'crosslingual15.jsonl': digest(RUNTIME / 'combined-questions.jsonl')}
    for model in MODELS:
        source = RUNTIME
        path = source / 'inference' / model / 'answers.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        assert len(rows) == 15
        outputs[model] = {r['id']: r for r in rows}
        assert set(outputs[model]) == {r['id'] for r in packet}
        source_hashes[model] = digest(path)
    rng = random.Random(34072027)
    # Four Latin blocks, drop one after shuffling: each position appears three or four times.
    permutations = []
    for _ in range(4):
        block = list(MODELS)
        rng.shuffle(block)
        permutations.extend(tuple(block[i:] + block[:i]) for i in range(4))
    rng.shuffle(permutations)
    permutations = permutations[:15]
    rng.shuffle(packet)
    records, key = [], []
    for row, order in zip(packet, permutations):
        rid = str(uuid.uuid5(uuid.NAMESPACE_URL, NAME + ':' + row['id']))
        fields = {'prompt': '\n\n'.join(m['role'].upper() + ':\n' + m['content'] for m in row['messages'])}
        for label, model in zip(LABELS, order):
            fields['answer_' + label.lower()] = outputs[model][row['id']]['prediction']
        records.append({'id': rid, 'fields': fields})
        key.append({'record_id': rid, 'dev_id': row['id'], 'models': dict(zip(LABELS, order))})
    assert all(sum(r['models'][label] == model for r in key) in (3, 4) for model in MODELS for label in LABELS)
    OUT.mkdir(parents=True, exist_ok=True)
    private = OUT / 'PRIVATE-model-key.json'
    payload = {'source_sha256': source_hashes, 'records': key}
    if private.exists():
        previous = json.loads(private.read_text(encoding='utf-8'))
        # Preserve the original key bytes; normalize the old metadata label only in memory.
        if 'holdout20.jsonl' in previous['source_sha256']:
            previous['source_sha256']['crosslingual15.jsonl'] = previous['source_sha256'].pop('holdout20.jsonl')
        assert previous == payload, 'Frozen private key differs'
    else:
        save(private, payload)
    save(OUT / 'anonymous-records.json', records)
    return records, source_hashes


def schema():
    return rg.Settings(
        guidelines=(
            'Compare the four answers to each prompt. Enter your order from best to worst and explain why. '
            'Example: A > C > B = D. Plain A C B D is also fine. Use every letter once. '
            'Ties are allowed; mention all-bad answers, missing information or uncertainty in your reasoning. '
            'Judge correctness, naturalness in the REQUIRED output language, meaning preservation and prompt constraints. Wrong-language answers violate the prompt. Numeric controls need only numbers. '
            'Do not reward length for its own sake. A-D identities change per prompt. '
            'Submit to save. No quality selections or additional scores. These are a tiny diagnostic holdout; once used for training decisions they are development data.'
        ),
        fields=[rg.TextField(name='prompt', title='Question', use_markdown=False)]
        + [rg.TextField(name='answer_' + c.lower(), title='Answer ' + c, use_markdown=False) for c in LABELS],
        questions=[
            rg.TextQuestion(name='ranking', title='Your order: best to worst', required=True,
                description='Use every letter once. Example: A > C > B = D. Ties use =.'),
            rg.TextQuestion(name='notes', title='Your reasoning', required=True,
                description='Explain your order, errors you noticed, ties, or why all answers are poor.'),
        ],
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
    assert result['total'] == 15
    for row in result['items']:
        rid = str(row.get('external_id') or row['id'])
        assert row['fields'] == expected[rid], 'Display roundtrip differs'
        assert not row.get('suggestions') and not row.get('metadata'), 'Nonblind annotations uploaded'
    receipt = {'dataset_id': str(dataset.id), 'name': NAME, 'workspace': workspace, 'records': 15,
               'url': url + f'/dataset/{dataset.id}/annotation-mode', 'added': len(pending),
               'per_record_randomization': True, 'balanced_positions': True,
               'model_identities_uploaded': False, 'automatic_scores_uploaded': False,
               'full_outputs_roundtrip_verified': True, 'source_sha256': hashes,
               'submitted': sum(any(r['status'] == 'submitted' for r in row.get('responses', [])) for row in result['items'])}
    save(OUT / 'receipt.json', receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
