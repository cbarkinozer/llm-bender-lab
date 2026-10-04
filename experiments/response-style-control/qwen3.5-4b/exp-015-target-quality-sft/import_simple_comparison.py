"""Create a simplified preference queue; preserve the detailed queue unchanged."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import urllib.request

from import_comparison import POSITIONS, balanced_mapping, load

SOURCE_ID = '3b2cf5b1-13d2-4ea1-859b-2faa16c029ad'
NAME = 'exp-015-016-simple-grades-32-v3'
PREVIOUS_ID = '5d0f657e-0abe-49cf-865b-d2800028a273'


def fetch(url, key, dataset_id):
    request = urllib.request.Request(
        f'{url}/api/v1/datasets/{dataset_id}/records?limit=100&include=responses',
        headers={'X-Argilla-Api-Key': key})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-root', type=Path, required=True)
    args = parser.parse_args()
    arms = load(args.results_root)
    baseline = arms['base'][1]
    mapping = balanced_mapping([row['id'] for row in baseline])
    private = args.results_root / 'blind-mapping-v1.json'
    assert json.loads(private.read_text(encoding='utf-8')) == mapping
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900')
    key = os.getenv('ARGILLA_API_KEY', 'argilla.apikey')
    original = fetch(url, key, SOURCE_ID)
    assert original['total'] == len(original['items']) == 32
    original_by_id = {row['external_id']: row for row in original['items']}
    indexed = {model: {row['id']: row for row in data}
               for model, (_, data) in arms.items()}
    fields = {}
    for row in baseline:
        item_id = row['id']
        old = original_by_id[item_id]['fields']
        conversation = '\n\n'.join(m['role'] + ': ' + m['content'] for m in row['messages'])
        assert old['conversation'] == conversation
        assert old['desired_answer'] == row['desired_answer']
        value = dict(conversation=conversation, desired_answer=row['desired_answer'])
        for position, model in mapping[item_id].items():
            answer = indexed[model][item_id]['answer']
            assert old['answer_' + position] == answer
            value['answer_' + position] = answer
        value['reference_note'] = old['reference_note']
        fields[item_id] = value

    import argilla as rg
    client = rg.Argilla(api_url=url, api_key=key)
    dataset = client.datasets(name=NAME, workspace='sft-review')
    if dataset is None:
        # Do not silently discard or invent annotations during a protocol change.
        assert not any(row.get('responses') for row in original['items']), (
            'Detailed reviews exist: preserve them and explicitly plan migration first')
        previous = fetch(url, key, PREVIOUS_ID)
        assert not any(row.get('responses') for row in previous['items']), (
            'Preference-only reviews exist: explicitly plan migration first')
        snapshot = args.results_root / 'queues-before-simple-grades-v3.json'
        assert not snapshot.exists(), 'Do not overwrite an earlier response snapshot'
        snapshot.write_text(json.dumps({'detailed': original, 'preference_only': previous},
                                       ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        guidelines = (
            'Soruyu, hedef cevabı ve dört çıktıyı oku. Önce doğru ve işe yarayan içeriği, '
            'sonra doğal Türkçeyi ve uygun uzunluğu değerlendir. Sadece kısa olması veya '
            'Markdown kullanmaması bir cevabı üstün yapmaz. Hedefle birebir aynı sözler şart değil. '
            'Her cevaba tek puan ver: pass=doğru ve yeterli; partial=kısmen doğru ama önemli '
            'eksik veya sorun var; fail=yanlış, temelsiz, çelişkili veya görevi karşılamıyor. '
            'En iyi için P/Q/R/S seç; ortak en iyiler varsa tie seç ve notta hangi '
            'cevapların eşit olduğunu belirt (ör. P ve R, veya hepsi). Hiçbiri kabul '
            'edilebilir değilse neither seç. Diğer durumlarda not isteğe bağlı. '
            'P/Q/R/S her soruda yeniden karıştırılır; sabit model isimleri değildir.')
        titles = dict(conversation='Soru / konuşma', desired_answer='Hedef cevap',
                      reference_note='Bu soruya özel not')
        titles.update({'answer_' + p: p + ' cevabı' for p in POSITIONS})
        settings = rg.Settings(
            guidelines=guidelines,
            fields=[rg.TextField(name=name, title=titles[name], use_markdown=False,
                                 required=name != 'reference_note')
                    for name in next(iter(fields.values()))],
            questions=[
                rg.LabelQuestion(name='best_output', title='En iyi cevap hangisi?',
                                 labels=[*POSITIONS, 'tie', 'neither'], required=True),
                *[rg.LabelQuestion(name=p + '_grade', title=p + ': pass / partial / fail',
                                   labels=['pass', 'partial', 'fail'], required=True)
                  for p in POSITIONS],
                rg.TextQuestion(name='notes', title='Kısa not (tie seçtiysen eşit cevapları belirt)',
                                required=False, use_markdown=False)])
        dataset = rg.Dataset(name=NAME, workspace='sft-review', settings=settings, client=client).create()
        dataset.records.log([rg.Record(id=item_id, fields=value)
                             for item_id, value in fields.items()])
    actual = fetch(url, key, dataset.id)
    assert actual['total'] == len(actual['items']) == 32
    assert {row['external_id']: row['fields'] for row in actual['items']} == fields
    assert [(q.name, q.required) for q in dataset.settings.questions] == [
        ('best_output', True), *[(p + '_grade', True) for p in POSITIONS], ('notes', False)]
    info = dict(name=NAME, id=str(dataset.id), count=32, blinded=True,
                url=f'{url}/dataset/{dataset.id}/annotation-mode?page=1&status=pending',
                source_dataset_id=SOURCE_ID, fields_verified=True,
                mapping_sha256=hashlib.sha256(private.read_bytes()).hexdigest(),
                scoring='best-output-with-explicit-tie-and-per-output-grades-v3',
                previous_simple_dataset_id=PREVIOUS_ID,
                original_queue_preserved=True)
    (args.results_root / 'argilla-simple-link.json').write_text(
        json.dumps(info, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(info))


if __name__ == '__main__':
    main()
