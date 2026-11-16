"""Migrate batch02 to input/thinking/output text editing, preserving owner edits."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

import argilla as rg
from dotenv import load_dotenv
import requests
from audit_turkish_sources import ROOT, OUT, filehash

DEST = OUT / 'review-local/batch02'
NAME = 'turkish-sft-train80-batch02-text-v02'
OLD_NAME = 'turkish-sft-train80-batch02-v01'


def split_answer(text):
    match = re.fullmatch(r'\s*<(think|thinking)>(.*?)</\1>\s*(.*?)\s*', text, re.S)
    if match:
        return match.group(2).strip(), match.group(3).strip()
    assert not re.search(r'</?(?:think|thinking)>', text), 'Malformed reasoning tags require inspection'
    return '', text


def main():
    load_dotenv(ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env')
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900').rstrip('/')
    api_key = os.getenv('ARGILLA_API_KEY', 'argilla.apikey')
    workspace = os.getenv('ARGILLA_WORKSPACE', 'sft-review')
    client = rg.Argilla(api_url=url, api_key=api_key)
    user = next(u for u in client.users if u.username == 'argilla')
    old = client.datasets(name=OLD_NAME, workspace=workspace)
    assert old is not None
    response = requests.get(url + f'/api/v1/datasets/{old.id}/records',
        params={'limit':100, 'include':'responses'}, headers={'X-Argilla-Api-Key':api_key}, timeout=30)
    response.raise_for_status()
    snapshot = response.json()
    assert snapshot['total'] == len(snapshot['items']) == 80
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    path = DEST / f'before-text-migration-{stamp}.json'
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    prior = {r['external_id']:r for r in snapshot['items']}
    rows = [json.loads(s) for s in (DEST / 'candidates80.jsonl').read_text(encoding='utf-8').splitlines()]
    assert set(prior) == {r['id'] for r in rows}
    dataset = client.datasets(name=NAME, workspace=workspace)
    if dataset is None:
        settings = rg.Settings(
            fields=[rg.TextField(name='original_input', title='Original input', use_markdown=False),
                    rg.TextField(name='original_thinking', title='Original thinking', required=False, use_markdown=False),
                    rg.TextField(name='original_output', title='Original output', use_markdown=False),
                    rg.TextField(name='source', title='Source / original system context', use_markdown=False)],
            questions=[rg.TextQuestion(name='input', title='Input', required=True),
                       rg.TextQuestion(name='thinking', title='Thinking (optional)', required=False,
                           description='Leave blank for a direct answer. Enter reasoning without think/thinking tags.'),
                       rg.TextQuestion(name='output', title='Output', required=True)],
            metadata=[rg.TermsMetadataProperty(name='source_key', options=['occam','sft','atlas','cot'])],
            guidelines='Edit the three textboxes in order: Input, Thinking (optional), Output. No ratings or keep/edit selections. Existing text is prefilled. Submit to save your final version. Leave Thinking blank if no separate reasoning is appropriate; an empty submitted Thinking box deliberately removes source reasoning. Do not put thinking tags in either textbox. All non-Occam source answers are untrusted candidates until your submitted final text. Occam retains standing owner approval; earlier submitted owner edits are carried over. Source originals remain visible for provenance. These are training candidates only; export still checks validity, leakage and token lengths.')
        dataset = rg.Dataset(name=NAME, workspace=workspace, settings=settings, client=client).create()
    assert [q.name for q in dataset.settings.questions] == ['input', 'thinking', 'output']
    existing = {str(r.id):r.to_dict() for r in dataset.records}
    assert set(existing) <= set(prior)
    records = []
    expected = {}
    migrated = []
    for row in rows:
        rid = row['id']; ms = row['original_messages']
        users = [m['content'] for m in ms if m['role']=='user']
        assert len(users) == 1 and all(m['role'] in ['system','user'] for m in ms[:-1]), 'Multi-turn input needs a dedicated representation'
        reason, answer = split_answer(ms[-1]['content'])
        fields = dict(original_input=users[0], original_thinking=reason, original_output=answer,
                      source=row['source_repo']+' @ '+row['source_revision']+'\n'+rid+'\n\nOriginal system:\n'+'\n'.join(m['content'] for m in ms if m['role']=='system'))
        responses = prior[rid].get('responses', [])
        assert len(responses) <= 1, 'Multiple reviewers require adjudication'
        values = responses[0]['values'] if responses else {}
        get = lambda key: values.get(key, {}).get('value')
        is_submitted = bool(responses and responses[0]['status']=='submitted')
        assert get('decision') not in ['reject','unsure'], 'Do not silently migrate rejected or unresolved records as accepted'
        corrected = get('corrected_answer')
        if corrected and corrected.strip(): reason, answer = split_answer(corrected)
        corrected_user = get('corrected_user')
        inp = corrected_user if corrected_user and corrected_user.strip() else users[0]
        assert inp.strip() and answer.strip()
        target = dict(input=inp, thinking=reason, output=answer)
        status = 'submitted' if is_submitted else 'draft'
        expected[rid] = dict(fields=fields, values=target, status=status)
        if rid in existing:
            assert existing[rid]['fields'] == fields
            continue
        records.append(rg.Record(id=rid, fields=fields, metadata={'source_key':rid.split(':')[0]},
            responses=[rg.Response(question_name=k, value=v, user_id=user.id, status=status) for k,v in target.items()]))
        if is_submitted: migrated.append(rid)
    if records: dataset.records.log(records, batch_size=20)
    response = requests.get(url + f'/api/v1/datasets/{dataset.id}/records',
        params={'limit':100, 'include':'responses'}, headers={'X-Argilla-Api-Key':api_key}, timeout=30)
    response.raise_for_status(); result = response.json()
    assert result['total'] == len(result['items']) == 80
    for row in result['items']:
        rid = row['external_id']; assert row['fields'] == expected[rid]['fields']
        if rid in existing: continue  # Preserve all later edits on reruns.
        assert len(row['responses']) == 1
        r = row['responses'][0]
        assert r['status'] == expected[rid]['status']
        assert {k:v['value'] for k,v in r['values'].items()} == expected[rid]['values']
    # Verify the original queue's saved annotations were not changed by migration.
    check = requests.get(url + f'/api/v1/datasets/{old.id}/records', params={'limit':100, 'include':'responses'},
        headers={'X-Argilla-Api-Key':api_key}, timeout=30)
    check.raise_for_status()
    assert {r['external_id']:r['responses'] for r in check.json()['items']} == {k:r['responses'] for k,r in prior.items()}, 'Source reviews changed concurrently; inspect migration snapshot'
    receipt = dict(name=NAME, dataset_id=str(dataset.id), url=url+f'/dataset/{dataset.id}/annotation-mode',
        records=80, question_order=['input','thinking','output'], completed=sum(any(a['status']=='submitted' for a in r['responses']) for r in result['items']),
        drafts=sum(any(a['status']=='draft' for a in r['responses']) for r in result['items']),
        old_dataset_id=str(old.id), snapshot=path.name, snapshot_sha256=filehash(path),
        original_queue_responses_unchanged=True, full_fields_and_prefilled_values_verified=True,
        export_policy='Only submitted text responses. Input/output required, optional thinking blank means NONE; never fall back to original reasoning. No quality label inferred.')
    (DEST / 'text-edit-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
