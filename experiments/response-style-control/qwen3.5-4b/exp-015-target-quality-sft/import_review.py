"""Create E/F draft review queues; verify fields, never overwrite annotations."""
import json
import os
import urllib.request
from prepare_pair import HERE,DRAFT,CONTROL_DRAFT,REPORT,load,sha,save,encoded

FIELDS=['conversation','previous_answer','proposed_answer','substance_check','skill','review_kind']

def payload(row,control=False):
    return dict(conversation=row['prompt_tr'],previous_answer=row.get('original_answer','—'),
        proposed_answer=row['desired_answer'],substance_check=row.get('reason') or row['evaluation_criteria'],
        skill=row['skill'],review_kind='control-reference' if control else row['review_kind'])

def snapshot(url,key,id_):
    request=urllib.request.Request(f'{url}/api/v1/datasets/{id_}/records?limit=100&include=responses',headers={'X-Argilla-Api-Key':key})
    with urllib.request.urlopen(request,timeout=30) as response:
        return json.load(response)

def main():
    import argilla as rg
    report=json.loads((HERE/REPORT).read_text(encoding='utf-8'))
    for path,hash_ in report['files'].items():
        assert sha((HERE.parent/path).read_bytes())==hash_,path
    url=os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900'); key=os.getenv('ARGILLA_API_KEY','argilla.apikey')
    client=rg.Argilla(api_url=url,api_key=key)
    links={}
    for kind,name,rows in [
        ('train','exp-015-016-target-quality-new-train-v1',load(HERE/DRAFT/'review-candidates.jsonl')),
        ('controls','exp-015-016-control-references-12-v2',load(HERE/CONTROL_DRAFT/'questions-12.jsonl'))]:
        control=kind=='controls'
        dataset=client.datasets(name=name,workspace='sft-review')
        guidelines=(
            'Exp015/016 hazırlığı. Bunlar model çıktısı değil, ajan tarafından yazılmış hedef cevap taslaklarıdır. '
            'Önce içerik doğruluğu, verilen bilgiye bağlılık, gerekli gerekçe ve doğal Türkçe; sonra uzunluk ve biçim. '
            'Çıkarımların kesinliğini abartmayın; kullanıcı tavsiye istemiyorsa çözüm dayatmayın. '
            'Kısa isim isteyen soruya açıklama eklemeyin; açıklama gereken yerde gerekçeyi silmeyin. '
            'accept: önerilen tam cevap uygun. rewrite: corrected_answer alanına istediğiniz tam cevabı yazın. '
            'reject: soruda/cevapta sorun var; notes alanında belirtin. Soruları sessizce değiştirmeyin. '
            'Bu ekrandaki kayıtlar tamamlanmadan eğitim açılmaz. '
            + ('Bu 12 kayıt yalnızca bağımsız kontrol referansıdır; hiçbir eğitimde kullanılmayacak. Referans tek geçerli ifade değildir: anlamca doğru farklı cevaplar kabul edilir.' if control else
               'repair kayıtlarında eski soru değişmiyor; previous_answer ile öneriyi karşılaştırın. new-train kayıtları yalnızca Exp016 için24 yeni eğitim örneğidir. Korunan15 doğru hedef için yeniden onay gerekmiyor.'))
        if dataset is None:
            settings=rg.Settings(guidelines=guidelines,
                fields=[rg.TextField(name=f,use_markdown=False) for f in FIELDS],
                questions=[rg.LabelQuestion(name='decision',title='Hedef cevap uygun mu?',labels=['accept','rewrite','reject'],required=True),
                    rg.TextQuestion(name='corrected_answer',title='Rewrite: istediğiniz tam cevap',use_markdown=False,required=False),
                    rg.TextQuestion(name='notes',title='Not veya soru düzeltme isteği',use_markdown=False,required=False)])
            dataset=rg.Dataset(name=name,workspace='sft-review',settings=settings,client=client).create()
            dataset.records.log([rg.Record(id=r['id'],fields=payload(r,control)) for r in rows])
        actual=snapshot(url,key,dataset.id)
        assert actual['total']==len(actual['items'])==len(rows)
        assert {r['external_id']:r['fields'] for r in actual['items']}=={r['id']:payload(r,control) for r in rows}
        links[kind]=dict(name=name,id=str(dataset.id),rows=len(rows),
            url=f'{url}/dataset/{dataset.id}/annotation-mode?page=1&status=pending',
            rows_sha256=sha(json.dumps(rows,ensure_ascii=False,sort_keys=True).encode()))
    save(HERE/'annotation-links-v2.json',encoded(links))
    print(json.dumps(links,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
