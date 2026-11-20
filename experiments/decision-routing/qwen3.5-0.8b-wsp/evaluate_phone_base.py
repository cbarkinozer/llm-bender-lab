"""Matched GPU generative phone baseline; distinct from historical A32 app-router."""
import argparse,hashlib,json,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('arm',choices=['parent','wsp']);a=p.parse_args()
    from vllm import LLM,SamplingParams
    from vllm.sampling_params import StructuredOutputsParams
    root=Path('/workspace/reflex-wsp');models=json.loads((root/'models.json').read_text())
    path=root/'data/routing-benchmarks/phone180.jsonl';rows=[json.loads(x) for x in path.read_text().splitlines()]
    out=root/'eval/phone-generative'/a.arm;out.mkdir(parents=True,exist_ok=False)
    llm=LLM(model=models[a.arm],dtype='bfloat16',max_model_len=4096,gpu_memory_utilization=.6,max_num_seqs=64,seed=3407)
    tok=llm.get_tokenizer();prompts=[]
    for r in rows:
        questions=json.loads(r['questions'])
        prompt='Select the best route for the request using this routing policy. Return only a JSON object with one key, "route", containing the selected route name.\nRouting policy:\n'+json.dumps(questions,ensure_ascii=False)+'\nRequest:\n'+r['state']
        prompts.append(tok.apply_chat_template([{'role':'user','content':prompt}],tokenize=False,add_generation_prompt=True,enable_thinking=False))
    routes=list(json.loads(rows[0]['questions'])['route']['criteria'])
    schema={'type':'object','properties':{'route':{'type':'string','enum':routes}},'required':['route'],'additionalProperties':False}
    settings={'temperature':0,'max_tokens':128,'seed':3407}
    manifest={'model':models[a.arm],'dataset_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'sampling':settings,
        'thinking':False,'dtype':'bfloat16','max_model_len':4096,'max_num_seqs':64,'structured_output_schema':schema,
        'prompt_sha256':hashlib.sha256(json.dumps(prompts).encode()).hexdigest(),'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'profile':'Matched GPU schema-based generative router; not a reproduction of historical A32 raw-HTTP app router or its latency'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    started=time.time();results=llm.generate(prompts,SamplingParams(**settings,structured_outputs=StructuredOutputsParams(json=schema)))
    records=[]
    for r,result in zip(rows,results):
        o=result.outputs[0]
        try:prediction=json.loads(o.text)['route']
        except (ValueError,KeyError):prediction=None
        gold=json.loads(r['gold'])['route']['label']
        records.append({'id':r['id'],'gold':gold,'prediction':prediction,'correct':prediction==gold,'text':o.text,'tokens':len(o.token_ids),'finish_reason':o.finish_reason})
    (out/'predictions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
    f1=[]
    for route in routes:
        tp=sum(r['gold']==route and r['prediction']==route for r in records)
        fp=sum(r['gold']!=route and r['prediction']==route for r in records)
        fn=sum(r['gold']==route and r['prediction']!=route for r in records)
        f1.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0)
    summary={'accuracy':sum(r['correct'] for r in records)/180,'macro_f1':sum(f1)/9,'rows':180,'errors':sum(r['prediction'] is None for r in records),'capped':sum(r['finish_reason']=='length' for r in records),'elapsed_seconds':time.time()-started}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary,flush=True)

if __name__=='__main__':main()
