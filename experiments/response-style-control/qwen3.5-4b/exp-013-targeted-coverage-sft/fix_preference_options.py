"""Clarify three-way ties without rewriting existing human responses."""
import argparse
import json
import os
from pathlib import Path
import urllib.request
import urllib.error
import argilla as rg


DATASET = 'e3b691cb-79fc-4bd8-a358-39f9a23770b5'
LABELS = ['A', 'C', 'D', 'A=C', 'A=D', 'C=D', 'A=C=D', 'neither']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot-dir', type=Path, required=True)
    args = parser.parse_args()
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900')
    key = os.getenv('ARGILLA_API_KEY', 'argilla.apikey')

    def request(path, body=None):
        req = urllib.request.Request(url + '/api/v1/' + path,
            data=None if body is None else json.dumps(body).encode(),
            headers={'X-Argilla-Api-Key': key, 'Content-Type': 'application/json'},
            method='GET' if body is None else 'PATCH')
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(error.read().decode()) from error

    path = f'datasets/{DATASET}'
    before = request(path + '/records?limit=100&include=responses')
    assert before['total'] == len(before['items']) == 20
    questions = request(path + '/questions')
    preferred = next(q for q in questions['items'] if q['name'] == 'preferred')
    legacy = [r['external_id'] for r in before['items']
              if any(x.get('values', {}).get('preferred', {}).get('value') == 'tie'
                     for x in r.get('responses', []))]
    args.snapshot_dir.mkdir(parents=True, exist_ok=False)
    (args.snapshot_dir / 'before.json').write_text(
        json.dumps({'records': before, 'questions': questions}, ensure_ascii=False, indent=2),
        encoding='utf-8')
    labels = {x: x for x in LABELS}
    if legacy:
        labels['tie'] = 'Legacy tie (unspecified; do not select)'
    description = ('Select the best answer or tied best answers. A=C means A and C tie ABOVE D; '
                   'likewise A=D and C=D. A=C=D means all three tie. '
                   'neither means none is acceptable. Do not use legacy tie.')
    # Published Argilla questions cannot change option count. Keep old queue intact.
    client = rg.Argilla(api_url=url, api_key=key)
    old = client.datasets(name='exp-013-014-A-C-D-validation-20', workspace='sft-review')
    name = 'exp-013-014-A-C-D-validation-20-v2'
    assert client.datasets(name=name, workspace='sft-review') is None, 'Never overwrite a reviewed queue'
    settings = rg.Settings(fields=list(old.settings.fields),
        questions=[rg.LabelQuestion(name='preferred', title=preferred['title'], labels=labels,
                    description=description, visible_labels=len(labels), required=True),
                   *[q for q in old.settings.questions if q.name != 'preferred']],
        guidelines=old.settings.guidelines + '\n\n' + description +
            '\nThis v2 queue preserves previous responses. Legacy tie on me-040 is ambiguous; '
            'reselect the actual tied best models rather than assuming all three tied.')
    dataset = rg.Dataset(name=name, workspace='sft-review', settings=settings, client=client).create()
    records = []
    for row in before['items']:
        responses = [rg.Response(question_name=q, value=value['value'], user_id=response['user_id'],
                                status=response['status'])
                     for response in row.get('responses', [])
                     for q, value in response['values'].items()]
        records.append(rg.Record(id=row['external_id'], fields=row['fields'], responses=responses))
    dataset.records.log(records)
    after = request(path + '/records?limit=100&include=responses')
    # No fields or reviews are written. Verify every stored response remains byte-equivalent in JSON.
    def content(records):
        return {r['id']: (r['fields'], r.get('responses', [])) for r in records['items']}
    assert content(before) == content(after), 'Existing content/reviews changed'
    updated = request(f'datasets/{dataset.id}/questions')
    actual = next(q for q in updated['items'] if q['name'] == 'preferred')
    assert [x['value'] for x in actual['settings']['options']] == list(labels)
    copied = request(f'datasets/{dataset.id}/records?limit=100&include=responses')
    def semantic(records):
        return {r['external_id']: (r['fields'], sorted(
            [(x['user_id'], x['status'], json.dumps(x['values'], sort_keys=True))
             for x in r.get('responses', [])])) for r in records['items']}
    assert copied['total'] == 20 and semantic(before) == semantic(copied)
    (args.snapshot_dir / 'after.json').write_text(
        json.dumps({'records': copied, 'questions': updated}, ensure_ascii=False, indent=2),
        encoding='utf-8')
    info = dict(dataset=str(dataset.id), name=name, labels=list(labels),
                legacy_tie_records=legacy, preserved_records=20,
                url=f'{url}/dataset/{dataset.id}/annotation-mode?page=1&status=pending')
    (args.snapshot_dir / 'link.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
    print(json.dumps(info))


if __name__ == '__main__':
    main()
