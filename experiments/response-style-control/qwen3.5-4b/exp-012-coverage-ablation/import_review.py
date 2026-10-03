"""Create only the 24 new B training drafts; never modify earlier annotations."""
import json
import os
from pathlib import Path
import urllib.request

import argilla as rg
from prepare_pair import encoded, load_rows, sha, save, HERE

NAME = 'exp-012-coverage-candidates-24'
FIELDS = ['conversation','proposed_answer','substance_check','category','replacement']

def payload(row):
    return dict(conversation='\n\n'.join(m['role']+': '+m['content'] for m in row['messages']),
        proposed_answer=row['desired_answer'], substance_check=row['evaluation_criteria'],
        category=row['category'],replacement=row['replaces_id'])

def main():
    draft=HERE/'data-draft-v1'
    manifest=json.loads((draft/'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        assert sha((draft/name).read_bytes()) == expected, name
    rows=load_rows(draft/'candidates-24.jsonl')
    assert len(rows)==24 and all(r['answer_status']=='draft-awaiting-human-review' for r in rows)
    url=os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900')
    key=os.getenv('ARGILLA_API_KEY','argilla.apikey')
    client=rg.Argilla(api_url=url,api_key=key)
    dataset=client.datasets(name=NAME,workspace='sft-review')
    if dataset is None:
        guidelines=('Yalnızca B deneyinin 24 yeni eğitim cevabını inceleyin. Önceki 56 onaylı kayıt ve '
            '20 validation sorusu değişmeyecek. Önce doğruluk, gerekçenin öneriye bağlantısı, belirsizlik '
            've doğal Türkçe; sonra gereksiz uzatma/biçim. Kısa olması tek başına başarı değil. '
            'Soru yeterliyse somut öneri verilmeli, bilgi eksikse yalnızca gerekli soru sorulmalı. '
            'Kişisel duygu, neden veya kullanıcı koşulu uydurmayın. Kabul için accept; cevabı değiştirmek '
            'için rewrite ve corrected_answer; uygun olmayan soru için reject ve notes. Sorunun kendisini '
            'değiştirmek gerekirse not yazın, alanları değiştirmeyin. Tüm 24 kayıt onaylanmadan B eğitime açılmaz. '
            'Bunlar yeni örneklerdir, base modelin cevaplarının özetleri değildir. Validation örneklerini buraya taşımayın.')
        settings=rg.Settings(guidelines=guidelines,
            fields=[rg.TextField(name=f,use_markdown=False) for f in FIELDS],
            questions=[rg.LabelQuestion(name='decision',title='Eğitim hedefi olarak uygun mu?',
                labels=['accept','rewrite','reject'],required=True),
                rg.TextQuestion(name='corrected_answer',title='Rewrite seçtiyseniz düzeltilmiş cevap',
                    use_markdown=False,required=False),
                rg.TextQuestion(name='notes',title='Sorun veya gerekçe (isteğe bağlı)',use_markdown=False,required=False)])
        dataset=rg.Dataset(name=NAME,workspace='sft-review',settings=settings,client=client).create()
        dataset.records.log([rg.Record(id=r['id'],fields=payload(r)) for r in rows])
    req=urllib.request.Request(f'{url}/api/v1/datasets/{dataset.id}/records?limit=100',
        headers={'X-Argilla-Api-Key':key})
    with urllib.request.urlopen(req,timeout=30) as response:
        items=json.load(response)['items']
    assert len(items)==24
    actual={r['external_id']:r['fields'] for r in items}
    assert actual=={r['id']:payload(r) for r in rows}, 'Existing queue differs; never overwrite reviews'
    info=dict(name=NAME,id=str(dataset.id),rows=24,
        url=f'{url}/dataset/{dataset.id}/annotation-mode?page=1&status=pending',
        candidate_sha256=sha((draft/'candidates-24.jsonl').read_bytes()))
    save(HERE/'annotation-link.json',encoded(info))
    print(json.dumps(info,ensure_ascii=False))

if __name__=='__main__':
    main()
