"""Import verified, per-item blinded base/C/E/F comparison; never modify reviews."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import random
import urllib.request

MODELS=('base','C','E','F')
POSITIONS=('P','Q','R','S')

def load(root):
    arms={}
    for model in MODELS:
        folder=root/(model+'-evaluation-v1')
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        assert manifest['status']=='completed' and manifest['count']==32
        assert hashlib.sha256((folder/'answers.jsonl').read_bytes()).hexdigest()==manifest['answers_sha256']
        data=[json.loads(s) for s in (folder/'answers.jsonl').read_text(encoding='utf-8').splitlines()]
        assert len(data)==len({r['id'] for r in data})==32
        arms[model]=(manifest,data)
    base_manifest,base=arms['base']
    for model,(manifest,data) in arms.items():
        for key in ('sources','ids','generation','seed','chat_template_sha256','backend','precision','revision','packages','batch_size'):
            assert manifest[key]==base_manifest[key],(model,key)
        for a,b in zip(data,base):
            for key in ('id','messages','desired_answer','rendered_prompt','prompt_token_ids','category','split'):
                assert a[key]==b[key],(model,a['id'],key)
    return arms

def balanced_mapping(ids):
    assert len(ids)==32 and len(set(ids))==32
    rng=random.Random(3407)
    assignments=[]
    for block in range(8):
        perm=list(MODELS); rng.shuffle(perm)
        assignments.extend([perm[shift:]+perm[:shift] for shift in range(4)])
    rng.shuffle(assignments)
    mapping={id:dict(zip(POSITIONS,assignment)) for id,assignment in zip(ids,assignments)}
    for position in POSITIONS:
        assert collections.Counter(m[position] for m in mapping.values())==dict.fromkeys(MODELS,8)
    return mapping

def main():
    p=argparse.ArgumentParser(); p.add_argument('--results-root',type=Path,required=True); a=p.parse_args()
    arms=load(a.results_root)
    baseline=arms['base'][1]
    mapping=balanced_mapping([r['id'] for r in baseline])
    private=a.results_root/'blind-mapping-v1.json'
    if private.exists():
        assert json.loads(private.read_text())==mapping
    else:
        private.write_text(json.dumps(mapping,indent=2)+'\n',encoding='utf-8')
    indexed={model:{r['id']:r for r in data} for model,(_,data) in arms.items()}
    fields={}
    for r in baseline:
        id=r['id']
        value=dict(conversation='\n\n'.join(m['role']+': '+m['content'] for m in r['messages']),
            desired_answer=r['desired_answer'],category=r['category'],evaluation_group=r['split'],
            reference_note=('Bu eski referans tartışmalı; kabul edilebilir alternatifleri içerik ölçütüne göre değerlendirin. '
                            'Bu madde hariç sonuç da raporlanacak.' if id=='me-089' else ''))
        for position,model in mapping[id].items():
            row=indexed[model][id]
            value['answer_'+position]=row['answer']
        value['termination']='; '.join(f"{position}: {indexed[model][id]['finish_reason']}, {indexed[model][id]['output_tokens']} token"
            for position,model in mapping[id].items())
        fields[id]=value
    import argilla as rg
    url=os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900'); key=os.getenv('ARGILLA_API_KEY','argilla.apikey')
    client=rg.Argilla(api_url=url,api_key=key)
    name='exp-015-016-blind-comparison-32-v1'
    dataset=client.datasets(name=name,workspace='sft-review')
    if dataset is None:
        guidelines=('Her maddede dört modelin konumu yeniden karıştırılmıştır; P/Q/R/S kalıcı model kimliği değildir. '
            'Önce içerik doğruluğu ve işe yararlılık, sonra doğal Türkçe, sonra ayrı biçim/üslup puanı verin. '
            'Hedefin sözcüklerini aynen kullanmak şart değil; doğru alternatifleri kabul edin. Kısa olmak tek başına başarı değildir. '
            'İçerik: pass=doğru ve gerekli bilgi/gerekçe/koşullar var; partial=kısmen işe yarıyor ama önemli eksik var; '
            'fail=yanlış, temelsiz, çelişkili veya görevi karşılamıyor. Türkçe: pass=doğal/doğru, partial=yerel pürüz, fail=ciddi bozukluk. '
            'Üslup: compliant=gereken kadar uzun, gereksiz süs/emoji/Markdown/soru/insansı iddia yok; partial=sınırlı sorun; '
            'noncompliant=belirgin sorun. Markdown tek başına içerik hatası değildir. Aynı cevaplara aynı puanı verin. '
            'En iyi bir veya birden fazla konumu seçin; birden fazla seçim yalnızca o cevapların ortak en iyi olduğunu belirtir. '
            'Hiçbiri kabul edilebilir değilse sadece neither seçin; neither ile bir konumu birlikte seçmeyin. '
            'Native EOS dışındaki sonlanmalar başarısız/eksik üretimdir; notta belirtin. me-089 referans notunu okuyun. '
            'Bu geliştirme ve tanısal kontrol değerlendirmesidir; bağımsız final benchmark sonucu değildir.')
        questions=[rg.MultiLabelQuestion(name='best_outputs',title='En iyi cevap(lar) hangisi?',
            labels=[*POSITIONS,'neither'],required=True)]
        for position in POSITIONS:
            for axis,labels,title in [('semantic',['pass','partial','fail'],'içerik ve işe yararlılık'),
                                      ('turkish',['pass','partial','fail'],'Türkçe'),
                                      ('style',['compliant','partial','noncompliant'],'biçim ve üslup')]:
                questions.append(rg.LabelQuestion(name=position+'_'+axis,title=position+': '+title,labels=labels,required=True))
        questions.append(rg.TextQuestion(name='notes',title='Belirleyici gerekçe / sorunlar',required=False,use_markdown=False))
        settings=rg.Settings(guidelines=guidelines,fields=[rg.TextField(name=f,use_markdown=False) for f in next(iter(fields.values()))],questions=questions)
        dataset=rg.Dataset(name=name,workspace='sft-review',settings=settings,client=client).create()
        dataset.records.log([rg.Record(id=id,fields=value) for id,value in fields.items()])
    request=urllib.request.Request(f'{url}/api/v1/datasets/{dataset.id}/records?limit=100&include=responses',headers={'X-Argilla-Api-Key':key})
    with urllib.request.urlopen(request,timeout=30) as response:
        actual=json.load(response)
    assert actual['total']==len(actual['items'])==32
    assert {r['external_id']:r['fields'] for r in actual['items']}==fields,'Never overwrite changed fields/reviews'
    info=dict(name=name,id=str(dataset.id),count=32,blinded=True,
        url=f'{url}/dataset/{dataset.id}/annotation-mode?page=1&status=pending',
        mapping_sha256=hashlib.sha256(private.read_bytes()).hexdigest(),fields_verified=True)
    (a.results_root/'argilla-link.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(info))

if __name__=='__main__':
    main()
