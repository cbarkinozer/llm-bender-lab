"""Create a corrected revision and merge only unchanged Argilla text targets."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import argilla as rg
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
PILOT = BASE / 'bilingual-pilot-v01'


def main():
    source = PILOT / 'data/train.jsonl'
    rows = [json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
    before = json.loads(json.dumps(rows))
    changes = []
    for row in rows:
        lang = row['output_language']
        gid = row['group_id']
        old = row['messages'][-1]['content']
        new = old
        if gid == 'bp01-g081' and lang == 'en':
            new = ('A semicolon joins the two independent clauses without a conjunction:\n\n'
                   'The sun set; the street lamps came on.\n\n'
                   'A comma alone would create a comma splice in standard written English. '
                   '“The sun having set, the street lamps came on” is another option, '
                   'but it makes the temporal relationship more explicit.\n')
        if gid == 'bp01-g088' and lang == 'en':
            assert 'both supervision and trust' in old
            new = old.replace('both supervision and trust', 'both supervision and safety')
        if gid == 'bp01-g153':
            note = ('Not: Ortalama yoğunluk koşulu (1,012 × 1,007 = 1,019084 g/cm³), hacim oranından hesaplanan '
                    'yoğunlukla (≈ 1,019583 g/cm³) tutarsızdır. Yukarıdaki hacimler yalnızca toplam hacim ve '
                    '1:1,4 oranı esas alınarak bulunmuştur; verilen koşulların tümü aynı anda sağlanamaz.'
                    if lang == 'tr' else
                    'Note: The average-density condition (1.012 × 1.007 = 1.019084 g/cm³) conflicts with the '
                    'density implied by the volume ratio (approximately 1.019583 g/cm³). The volumes above '
                    'use only the total volume and the 1:1.4 ratio; not all stated conditions can hold simultaneously.')
            new = old.rstrip() + '\n\n' + note + '\n'
        if new != old:
            row['messages'][-1]['content'] = new
            row['quality_status'] = 'agent-corrected; owner review pending'
            row['correction_revision'] = 'v01-corrections-01'
            changes.append(dict(id=row['id'], group_id=gid, field='assistant.content', before=old, after=new))
    assert len(changes) == 8
    dest = PILOT / 'revisions/v01-corrections-01'
    dest.mkdir(parents=True, exist_ok=True)
    def write(name, selected):
        content = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in selected)
        path = dest / name
        if path.exists():
            assert path.read_text(encoding='utf-8') == content
        else:
            path.write_text(content, encoding='utf-8', newline='\n')
        return hashlib.sha256(path.read_bytes()).hexdigest()
    hashes = {'train.jsonl': write('train.jsonl', rows),
              'train-arm-a-tr-only.jsonl': write('train-arm-a-tr-only.jsonl', [r for r in rows if r['direction'] == 'tr-tr'])}
    load_dotenv(ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env')
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900').rstrip('/')
    key = os.getenv('ARGILLA_API_KEY', 'argilla.apikey')
    client = rg.Argilla(api_url=url, api_key=key)
    dataset = client.datasets(name='turkish-bilingual-pilot160-text-v01', workspace='sft-review')
    def fetch():
        items = []
        for offset in (0, 100):
            response = requests.get(f'{url}/api/v1/datasets/{dataset.id}/records',
                params={'limit': 100, 'offset': offset, 'include': 'responses'}, headers={'X-Argilla-Api-Key': key}, timeout=30)
            response.raise_for_status()
            items.extend(response.json()['items'])
        return {r['external_id']: r for r in items}
    snapshot = fetch()
    backup = BASE / 'crosslingual-runtime-local/bilingual-review-backups'
    backup.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    (backup / f'before-corrections-{stamp}.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')
    updated, preserved = [], []
    for gid in ('bp01-g081', 'bp01-g088', 'bp01-g153'):
        record = snapshot[gid]
        fields = dict(record['fields'])
        relevant = [c for c in changes if c['group_id'] == gid and c['id'].endswith(('-tr-tr', '-en-en'))]
        for change in relevant:
            k = 'tr_output' if change['id'].endswith('-tr-tr') else 'en_output'
            assert fields['original_' + k] in (change['before'], change['after'])
            fields['original_' + k] = change['after']
        responses = []
        for response in record['responses']:
            for k, obj in response['values'].items():
                value = obj['value']
                for change in relevant:
                    target = 'tr_output' if change['id'].endswith('-tr-tr') else 'en_output'
                    if k == target:
                        if value == change['before']:
                            value = change['after']
                        elif value != change['after']:
                            preserved.append(dict(group_id=gid, field=k))
                responses.append(rg.Response(question_name=k, value=value, user_id=response['user_id'], status=response['status']))
        # Recheck immediately before updating; never merge against a stale owner review.
        assert fetch()[gid]['responses'] == record['responses'], 'Concurrent owner edit; rerun'
        dataset.records.log([rg.Record(id=gid, fields=fields, responses=responses)])
        updated.append(gid)
    actual = fetch()
    for gid in snapshot:
        if gid not in updated:
            assert actual[gid]['fields'] == snapshot[gid]['fields']
            assert actual[gid]['responses'] == snapshot[gid]['responses']
        else:
            assert len(actual[gid]['responses']) == len(snapshot[gid]['responses'])
            relevant = [c for c in changes if c['group_id'] == gid and c['id'].endswith(('-tr-tr', '-en-en'))]
            for change in relevant:
                k = 'tr_output' if change['id'].endswith('-tr-tr') else 'en_output'
                assert actual[gid]['fields']['original_' + k] == change['after']
            for prior in snapshot[gid]['responses']:
                current = next(r for r in actual[gid]['responses'] if r['user_id'] == prior['user_id'])
                assert current['status'] == prior['status']
                expected = {k: v['value'] for k, v in prior['values'].items()}
                for change in relevant:
                    k = 'tr_output' if change['id'].endswith('-tr-tr') else 'en_output'
                    if expected.get(k) == change['before']:
                        expected[k] = change['after']
                assert {k: v['value'] for k, v in current['values'].items()} == expected
    manifest = dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), artifacts=hashes,
        changes=changes, updated_argilla_groups=updated, owner_edits_preserved=preserved,
        note='Original artifacts, frozen eval and existing plans unchanged. Recompute token budgets, validation and plan references before training this revision. g012 grammar explanation remains flagged for separate review.')
    (dest / 'corrections.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(revision=str(dest), changed_rows=len(changes), updated_groups=updated, owner_edits_preserved=preserved), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
