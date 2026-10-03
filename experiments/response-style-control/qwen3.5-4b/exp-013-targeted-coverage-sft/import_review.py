"""Create only the twelve shared C/D candidates; never overwrite existing reviews."""
import json
import os
import urllib.request
from prepare_next_pair import HERE, candidates, sha, save, encoded, load_rows

NAME = 'exp-013-014-targeted-candidates-12-v2'
FIELDS = ['conversation','proposed_answer','substance_check','category','replacement']


def payload(row):
    return dict(conversation=row['prompt_tr'], proposed_answer=row['desired_answer'],
        substance_check=row['evaluation_criteria'], category=row['category'], replacement=row['replaces_id'])


def main():
    import argilla as rg
    draft = HERE/'data-draft-v2'
    manifest = json.loads((draft/'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        assert sha((draft/name).read_bytes()) == expected, name
    rows = load_rows(draft/'candidates-12.jsonl')
    assert rows == candidates() and len(rows) == 12
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900')
    key = os.getenv('ARGILLA_API_KEY', 'argilla.apikey')
    client = rg.Argilla(api_url=url, api_key=key)
    dataset = client.datasets(name=NAME, workspace='sft-review')
    if dataset is None:
        guidelines = (
            'Bu 12 yeni eğitim kaydı C ve D deneylerinde ortak kullanılacak. '
            'A deneyinin diğer 68 kaydı ve 20 validation sorusu değişmiyor. '
            'Önce doğruluk, doğal Türkçe, gerekçe ve verilen bilgiye bağlılık; sonra uzunluk ve biçim. '
            'Kesin neden yalnızca kanıt varsa söylenmeli; bilinmeyen niyet veya koşul uydurulmamalı. '
            'İstenen kişi/nesne/sayı doğru seçilmeli; belirsizlik ve koşullar korunmalı. '
            'accept: cevap uygun. rewrite: corrected_answer alanına istediğiniz tam cevabı yazın. '
            'reject: soru uygun değil; notes alanına nedenini yazın. '
            'Soruyu değiştirmek gerekiyorsa not bırakın, sessizce alanları değiştirmeyin. '
            'Bunlar yeni yazılmış taslaklardır, base cevaplarının özetleri değildir. '
            'Tüm 12 kayıt onaylanmadan iki deney de eğitime açılmayacak. '
            'Validation sorularını veya yakın senaryolarını bu eğitim kaydına taşımayın.')
        settings = rg.Settings(guidelines=guidelines,
            fields=[rg.TextField(name=f, use_markdown=False) for f in FIELDS],
            questions=[rg.LabelQuestion(name='decision', title='Eğitim hedefi olarak uygun mu?',
                labels=['accept','rewrite','reject'], required=True),
                rg.TextQuestion(name='corrected_answer', title='Rewrite için düzeltilmiş tam cevap',
                    use_markdown=False, required=False),
                rg.TextQuestion(name='notes', title='Sorun veya gerekçe', use_markdown=False, required=False)])
        dataset = rg.Dataset(name=NAME, workspace='sft-review', settings=settings, client=client).create()
        dataset.records.log([rg.Record(id=r['id'], fields=payload(r)) for r in rows])
    req = urllib.request.Request(f'{url}/api/v1/datasets/{dataset.id}/records?limit=100&include=responses',
        headers={'X-Argilla-Api-Key':key})
    with urllib.request.urlopen(req, timeout=30) as response:
        actual = json.load(response)
    assert actual['total'] == len(actual['items']) == 12
    assert {r['external_id']:r['fields'] for r in actual['items']} == {r['id']:payload(r) for r in rows}
    info = dict(name=NAME, id=str(dataset.id), rows=12,
        url=f'{url}/dataset/{dataset.id}/annotation-mode?page=1&status=pending',
        candidate_sha256=sha((draft/'candidates-12.jsonl').read_bytes()))
    save(HERE/'annotation-link-v2.json', encoded(info))
    print(json.dumps(info, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
