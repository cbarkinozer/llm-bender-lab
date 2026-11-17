"""Publish grouped bilingual text editing without changing existing annotations."""
import hashlib
import json
import os
from pathlib import Path

import argilla as rg
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b/bilingual-pilot-v01'
NAME = 'turkish-bilingual-pilot160-text-v01'


def main():
    source = BASE / 'data/train.jsonl'
    rows = [json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
    groups = {}
    for row in rows:
        groups.setdefault(row['group_id'], {})[row['direction']] = row
    assert len(rows) == 640 and len(groups) == 160
    flags = {}
    for line in (BASE / 'data/translation-flags.jsonl').read_text(encoding='utf-8').splitlines():
        flag = json.loads(line)
        flags.setdefault(flag['group_id'], []).append(flag)
    corrections = {r['group_id']: r for r in json.loads((BASE / 'reports/proposed-corrections.json').read_text(encoding='utf-8'))}
    load_dotenv(ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env')
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900').rstrip('/')
    client = rg.Argilla(api_url=url, api_key=os.getenv('ARGILLA_API_KEY', 'argilla.apikey'))
    workspace = os.getenv('ARGILLA_WORKSPACE', 'sft-review')
    owner = next(u for u in client.users if u.username == 'argilla')
    keys = [f'{lang}_{part}' for lang in ('tr', 'en') for part in ('input', 'thinking', 'output')]
    dataset = client.datasets(name=NAME, workspace=workspace)
    if dataset is None:
        settings = rg.Settings(
            fields=[rg.TextField(name='context', title='Task / system instructions / flagged issues', use_markdown=False)]
            + [rg.TextField(name='original_' + k, title='Original ' + k, required=False, use_markdown=False) for k in keys],
            questions=[rg.TextQuestion(name=k, title=k.replace('_', ' ').title(), required=not k.endswith('thinking'),
                description='Optional reasoning without tags; blank means no reasoning.' if k.endswith('thinking') else 'Edit the complete text; submit to save.') for k in keys]
            + [rg.TextQuestion(name='notes', title='Notes / unresolved issue or exclusion request', required=False)],
            guidelines='Review one underlying task at a time, covering all four language directions. Edit Turkish Input, Thinking, Output, then English Input, Thinking, Output. Text is prefilled. No ratings. Preserve meaning, numbers, constraints and negation across languages. Thinking is optional; blank intentionally removes it. No think tags. Inputs include target-language suffixes: these will be reapplied per direction on export, not copied blindly. System prompts are shown in context. Flag conflicting language-bound tasks or request exclusion in Notes. Submit saves your review. Drafts are not approvals. Proposed corrections are suggestions only and have NOT been applied. This queue contains training candidates only, never fresh evaluation references.')
        dataset = rg.Dataset(name=NAME, workspace=workspace, settings=settings, client=client).create()
    assert [q.name for q in dataset.settings.questions] == keys + ['notes']
    existing = {str(r.id): r.to_dict() for r in dataset.records}
    assert set(existing) <= set(groups)
    expected, records = {}, []
    for gid, variants in sorted(groups.items()):
        assert set(variants) == {'tr-tr', 'en-tr', 'tr-en', 'en-en'}
        values, systems = {}, {}
        for lang in ('tr', 'en'):
            row = variants[f'{lang}-{lang}']
            users = [m['content'] for m in row['messages'] if m['role'] == 'user']
            assert len(users) == 1 and row['messages'][-1]['role'] == 'assistant'
            values[f'{lang}_input'] = users[0]
            values[f'{lang}_thinking'] = row.get('worked_solution') or ''
            values[f'{lang}_output'] = row['messages'][-1]['content']
            systems[lang] = [m['content'] for m in row['messages'] if m['role'] == 'system']
        context = dict(group_id=gid, source=variants['tr-tr']['source_row_id'],
                       systems=systems, flags=flags.get(gid, []), proposed_correction=corrections.get(gid),
                       variant_language_instructions={d: r.get('language_instruction') for d, r in variants.items()})
        fields = dict(context=json.dumps(context, ensure_ascii=False, indent=2), **{'original_' + k: v for k, v in values.items()})
        expected[gid] = fields
        if gid in existing:
            assert existing[gid]['fields'] == fields, 'Existing queue differs; create a new revision instead'
            continue
        records.append(rg.Record(id=gid, fields=fields, responses=[rg.Response(question_name=k, value=v, user_id=owner.id, status='draft') for k, v in values.items()]))
    if records:
        dataset.records.log(records, batch_size=20)
    items = []
    for offset in (0, 100):
        result = requests.get(f'{url}/api/v1/datasets/{dataset.id}/records',
            params={'limit': 100, 'offset': offset, 'include': 'responses'},
            headers={'X-Argilla-Api-Key': os.getenv('ARGILLA_API_KEY', 'argilla.apikey')}, timeout=30)
        result.raise_for_status()
        items.extend(result.json()['items'])
    actual = {r['external_id']: r for r in items}
    assert set(actual) == set(expected)
    for gid, record in actual.items():
        assert record['fields'] == expected[gid]
        if record['responses'] and record['responses'][0]['status'] == 'draft':
            response = record['responses'][0]
            assert response['status'] == 'draft'
            assert {k: v['value'] for k, v in response['values'].items()} == {k: expected[gid]['original_' + k] for k in keys}
    receipt = dict(name=NAME, dataset_id=str(dataset.id), records=len(actual), added=len(records),
                   source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                   url=f'{url}/dataset/{dataset.id}/annotation-mode', grouped_directions=4,
                   full_fields_and_prefilled_values_verified=True)
    destination = BASE / 'inspection/argilla-review-receipt.json'
    destination.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
