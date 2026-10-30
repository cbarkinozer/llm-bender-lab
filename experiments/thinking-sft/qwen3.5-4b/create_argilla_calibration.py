"""Create a small original-training-only reasoning calibration in Argilla."""
import json
from pathlib import Path
import argilla as rg

ROOT=Path(__file__).resolve().parents[3]
ENV=ROOT/'experiments/unit-test-generation/qwen3.5-4b/review/.env'
SOURCE=ROOT/'experiments/response-style-control/qwen3.5-4b/exp-016-diverse-coverage-sft/data-reviewed-v1/train-reviewed.jsonl'
TRACES={
 'tc-009':'Soru bir kişiye siz diye hitap ediyor; yüklemin kişi eki de siz hitabıyla uyumlu olmalı. Geçmiş zaman ve soru anlamı korunur.',
 'tc-010':'Derya doktora programına başvuruyor; doktora burada lisansüstü eğitimi belirtir. Kerem ise doktor mesleğinde çalışıyor.',
 'me-005':'Cümlede yönelme eki isimden ayrı yazılmış: rapor a yerine rapora yazılmalı. Diğer bilgileri ve anlamı korurum.',
 'me-006':'Ayrılma anlamı binadan biçiminde bitişik yazılır. İki bağımsız yargı noktalı virgülle ayrılabilir; olayların anlamı korunur.'}

def main():
 env=dict(line.split('=',1) for line in ENV.read_text().splitlines() if line and not line.startswith('#'))
 client=rg.Argilla(api_url='http://127.0.0.1:7900',api_key=env['ARGILLA_API_KEY'])
 name='occam2-thinking-calibration-v01';workspace=env['ARGILLA_WORKSPACE']
 old=client.datasets(name=name,workspace=workspace)
 if old is not None:
  print(json.dumps({'dataset_id':str(old.id),'url':f'http://127.0.0.1:7900/dataset/{old.id}/annotation-mode','status':'existing-preserved'}));return
 rows=[json.loads(l) for l in SOURCE.read_text().splitlines()];selected=[r for r in rows if r['id'] in TRACES]
 assert len(selected)==len(TRACES) and all(r['split']=='train' and not r['evaluation_only'] for r in selected)
 settings=rg.Settings(fields=[rg.TextField(name='prompt',title='Orijinal eğitim sorusu'),rg.TextField(name='reasoning',title='Önerilen Türkçe düşünme'),rg.TextField(name='answer',title='Mevcut nihai yanıt')],questions=[rg.LabelQuestion(name='decision',title='Bu örneği düşünme SFT için nasıl değerlendirelim?',labels=['Uygun','Düzeltme gerekli','Düşünme gereksiz','Emin değilim'],required=True),rg.TextQuestion(name='notes',title='Düzeltme veya yorum',required=False)])
 dataset=rg.Dataset(name=name,workspace=workspace,settings=settings,client=client);dataset.create()
 dataset.records.log([rg.Record(id=r['id'],fields={'prompt':json.dumps(r['messages'],ensure_ascii=False,indent=2),'reasoning':TRACES[r['id']],'answer':r['desired_answer']}) for r in selected])
 print(json.dumps({'dataset_id':str(dataset.id),'url':f'http://127.0.0.1:7900/dataset/{dataset.id}/annotation-mode','records':len(selected),'status':'created'}))
if __name__=='__main__':main()
