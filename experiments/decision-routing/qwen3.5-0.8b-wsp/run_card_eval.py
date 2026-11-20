"""Matched think35 replication. Batch scheduling differs from upstream; all samples retained."""
import os,json,time,argparse,hashlib,gzip,sys
from pathlib import Path
os.environ['HF_HOME']='/workspace/.cache/huggingface'
ROOT=Path('/workspace/reflex-wsp')
# Only the unavailable, unused loop detector import is removed; math grading stays upstream.
source=Path('/workspace/repos/lm_understand-logs/exp8_math/code/mathqa.py').read_text()
a=source.index('try:   # the multiple-choice'); b=source.index('\nREPO =',a)
source=source[:a]+"def mcqa_loop_signals(text):\n    raise RuntimeError('Unused upstream loop detector unavailable')\n"+source[b:]
import types
Q=types.ModuleType('mathqa'); Q.__file__=str(ROOT/'tools/mathqa.py'); exec(compile(source,Q.__file__,'exec'),Q.__dict__)
from instruction_following_eval import instructions_registry as IR

def grade(r,text):
    if r.get('kind')!='ifeval':
        pred,_=Q.extract(text);return {'correct':Q.is_correct(pred,r['answer']),'pred':pred}
    resp=text.split('</think>')[-1].strip() if '</think>' in text else ''
    follow=[]
    for iid,kw in zip(r['instruction_id_list'],r['kwargs']):
        ins=IR.INSTRUCTION_DICT[iid](iid)
        ins.build_description(**{k:v for k,v in (kw or {}).items() if v is not None})
        args=ins.get_instruction_args()
        if args and 'prompt' in args:ins.build_description(prompt=r['prompt'])
        follow.append(bool(resp) and bool(ins.check_following(resp)))
    return {'correct':all(follow),'instruction_following':follow}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('arm',choices=['wsp','parent']);ap.add_argument('--smoke',action='store_true');args=ap.parse_args()
    from transformers import AutoTokenizer
    from vllm import LLM,SamplingParams
    ckpt=json.loads((ROOT/'models.json').read_text())[args.arm]
    out=ROOT/'eval'/('smoke' if args.smoke else 'card')/args.arm;out.mkdir(parents=True,exist_ok=True)
    tok=AutoTokenizer.from_pretrained(ckpt)
    settings=dict(temperature=.6,top_p=.95,top_k=20,presence_penalty=1.5,max_tokens=32768,seed=0)
    manifest={'model':ckpt,'sampling':settings,'thinking':True,'batch_problems':32,'max_num_seqs':128,'max_model_len':34816,'dtype':'bfloat16','upstream':'4d09ba6d6a7e891dd8063974dfe81b3d78e3494f','runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    mp=out/'manifest.json'
    if mp.exists() and json.loads(mp.read_text())!=manifest:raise RuntimeError('Run manifest changed')
    mp.write_text(json.dumps(manifest,indent=2))
    llm=LLM(model=ckpt,dtype='bfloat16',gpu_memory_utilization=.85,max_model_len=34816,max_num_seqs=128,seed=0)
    if args.smoke:
        prompt=tok.apply_chat_template([{'role':'user','content':'What is 2 + 2? Put your final answer in \\boxed{}.'}],tokenize=False,add_generation_prompt=True,enable_thinking=True)
        result=llm.generate([prompt],SamplingParams(n=1,**{**settings,'max_tokens':256}))
        s=result[0].outputs[0];(out/'output.json').write_text(json.dumps({'text':s.text,'tokens':len(s.token_ids),'finish_reason':s.finish_reason,'grade':grade({'answer':'4'},s.text)},indent=2));print('SMOKE_OK',flush=True);return
    for name,n in [('math500',4),('gsm8k',2),('ifeval',2)]:
        rows=[json.loads(l) for l in (ROOT/'bench'/f'{name}.jsonl').read_text().splitlines()]
        for start in range(0,len(rows),32):
            dest=out/f'{name}_{start:04d}.jsonl.gz'
            if dest.exists():continue
            batch=rows[start:start+32];t=time.time()
            prompts=[tok.apply_chat_template([{'role':'user','content':r['prompt'] if r.get('kind') else Q.build_prompt(r['problem'])}],tokenize=False,add_generation_prompt=True,enable_thinking=True) for r in batch]
            results=llm.generate(prompts,SamplingParams(n=n,**settings));records=[]
            for r,o in zip(batch,results):
                for sample,s in enumerate(o.outputs):
                    if s.finish_reason not in ('stop','length'):raise RuntimeError('Incomplete generation')
                    records.append({'id':r['id'],'sample':sample,'text':s.text,'tokens':len(s.token_ids),'finish_reason':s.finish_reason,'stop_reason':s.stop_reason,**grade(r,s.text)})
            tmp=dest.with_suffix('.tmp')
            with gzip.open(tmp,'wt') as f:
                for r in records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
            tmp.replace(dest)
            allrows=[]
            for p in sorted(out.glob(f'{name}_*.jsonl.gz')):
                with gzip.open(p,'rt') as f:allrows.extend(json.loads(l) for l in f)
            summary={'name':name,'completed_samples':len(allrows),'expected_samples':len(rows)*n,'accuracy':sum(r['correct'] for r in allrows)/len(allrows),'cut_share':sum(r['finish_reason']=='length' for r in allrows)/len(allrows),'tokens_sum':sum(r['tokens'] for r in allrows),'last_batch_seconds':round(time.time()-t,2)}
            (out/f'{name}_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
if __name__=='__main__':main()