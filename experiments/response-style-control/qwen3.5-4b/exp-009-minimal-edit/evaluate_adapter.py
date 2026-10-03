"""Generate final-adapter answers to the frozen 20 development prompts."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time

HERE=Path(__file__).resolve().parent
REV='3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636'

def repeated_tail(tokens):
    """Conservative exact-token loop diagnostic, not a semantic quality score."""
    for width in range(32,min(512,len(tokens)//4)+1):
        if tokens[-width:]*4==tokens[-4*width:]:
            return width
    return None

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--adapter',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--bounded',action='store_true',help='Stop exact loops/timeouts; no expanded-budget retries')
    p.add_argument('--resume-from',type=Path,help='Reuse completed EOS answers with matching adapter/input identity')
    a=p.parse_args()
    if a.output_dir.exists():
        raise ValueError('Refusing overwrite')
    from unsloth import FastLanguageModel
    from peft import PeftModel
    import torch
    from transformers import AutoTokenizer, StoppingCriteria, StoppingCriteriaList, set_seed
    set_seed(3407)
    model,_=FastLanguageModel.from_pretrained(model_name='unsloth/Qwen3.5-4B',revision=REV,
        max_seq_length=32768,load_in_4bit=False,load_in_16bit=True,full_finetuning=False)
    model=PeftModel.from_pretrained(model,str(a.adapter),is_trainable=False)
    assert any('lora_' in n for n,_ in model.named_parameters())
    FastLanguageModel.for_inference(model)
    model.eval()
    tok=AutoTokenizer.from_pretrained('unsloth/Qwen3.5-4B',revision=REV)
    source=HERE/'reviewed-v2/validation-reviewed.jsonl'
    rows=[json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
    assert len(rows)==20 and all(r['evaluation_only'] and r['split']=='validation' and r['base_comparison_eligible'] for r in rows)
    expected=json.loads((HERE/'training-preflight-v1/training-config.json').read_text())['dataset']['hashes']['validation-reviewed.jsonl']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
    a.output_dir.mkdir(parents=True)
    budgets=[4096] if a.bounded else [4096,8192,16384]
    manifest=dict(status='running',model='unsloth/Qwen3.5-4B',revision=REV,adapter=str(a.adapter),
        adapter_hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in a.adapter.glob('*') if f.is_file()},
        validation_sha256=expected,ids=[r['id'] for r in rows],seed=3407,
        generation=dict(do_sample=False,num_beams=1,repetition_penalty=1.05,budgets=budgets,thinking=False,additional_system_prompt=None,
            safety_policy='exact token loop (32..512 token period repeated 4 times) or 180 seconds; failure not EOS' if a.bounded else 'original wide-budget retries'),
        backend='Unsloth/Transformers',precision='BF16',batch_size=1,
        comparison_caveat='Base used vLLM 0.20.1 / Torch 2.11; adapter uses Unsloth/Transformers / Torch 2.7.1. Semantic prompts, template and decoding policy match; numerical/backend parity is not exact.',
        packages={n:importlib.metadata.version(n) for n in ['torch','transformers','unsloth','peft']},
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip(),
        chat_template_sha256=hashlib.sha256(tok.chat_template.encode()).hexdigest(),
        eos_token_ids=model.generation_config.eos_token_id)
    def write_manifest():
        (a.output_dir/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    write_manifest()
    answers=[]
    eos=model.generation_config.eos_token_id
    eos=[eos] if isinstance(eos,int) else eos
    assert eos
    reused={}
    if a.resume_from:
        previous=json.loads((a.resume_from/'manifest.json').read_text(encoding='utf-8'))
        assert previous['adapter_hashes']==manifest['adapter_hashes']
        assert previous['validation_sha256']==manifest['validation_sha256']
        for line in (a.resume_from/'answers.jsonl').read_text(encoding='utf-8').splitlines():
            saved=json.loads(line)
            if saved['native_eos']:
                reused[saved['id']]=saved
        manifest['reused_from']=str(a.resume_from)
        manifest['reused_ids']=list(reused)
        write_manifest()
    with (a.output_dir/'attempts.jsonl').open('w',encoding='utf-8') as attempts, (a.output_dir/'answers.jsonl').open('w',encoding='utf-8') as output:
        for r in rows:
            ids=tok.apply_chat_template(r['messages'],tokenize=True,add_generation_prompt=True,enable_thinking=False)
            if r['id'] in reused:
                saved=reused[r['id']]
                assert saved['messages']==r['messages'] and saved['prompt_token_ids']==ids
                saved['finish_reason']='native_eos'; saved['reused']=True
                output.write(json.dumps(saved,ensure_ascii=False)+'\n'); output.flush()
                answers.append(saved)
                print(r['id'],'REUSED EOS',flush=True)
                continue
            x=torch.tensor([ids],device=next(model.parameters()).device)
            complete=False
            for budget in budgets:
                started=time.time()
                class Guard(StoppingCriteria):
                    reason=None
                    def __call__(self,input_ids,scores,**kwargs):
                        count=input_ids.shape[1]-len(ids)
                        if count%16==0:
                            current=input_ids[0,len(ids):].tolist()
                            width=repeated_tail(current)
                            if width:
                                self.reason='repetition_guard'
                            if count%128==0:
                                (a.output_dir/'progress.json').write_text(json.dumps(dict(id=r['id'],output_tokens=count,elapsed=time.time()-started,token_ids=current))+'\n')
                        if self.reason is None and time.time()-started>180:
                            self.reason='wall_time_guard'
                        return self.reason is not None
                guard=Guard()
                with torch.inference_mode():
                    y=model.generate(input_ids=x,attention_mask=torch.ones_like(x),do_sample=False,num_beams=1,
                        repetition_penalty=1.05,max_new_tokens=budget,eos_token_id=eos,pad_token_id=tok.pad_token_id,
                        forced_eos_token_id=None,use_cache=True,
                        stopping_criteria=StoppingCriteriaList([guard]) if a.bounded else None)
                tokens=y[0,len(ids):].tolist()
                complete=bool(tokens and tokens[-1] in eos)
                answer=tok.decode(tokens,skip_special_tokens=True)
                result=dict(id=r['id'],category=r['category'],messages=r['messages'],original_answer=r['original_answer'],
                    desired_answer=r['desired_answer'],adapter_answer=answer,prompt_token_ids=ids,output_token_ids=tokens,
                    output_tokens=len(tokens),budget=budget,native_eos=complete,seconds=time.time()-started,
                    finish_reason='native_eos' if complete else guard.reason or 'length_limit')
                attempts.write(json.dumps(result,ensure_ascii=False)+'\n'); attempts.flush()
                del y
                if complete:
                    break
            output.write(json.dumps(result,ensure_ascii=False)+'\n'); output.flush()
            answers.append(result)
            print(r['id'],len(tokens),'EOS' if complete else 'LENGTH_LIMIT',flush=True)
    with (a.output_dir/'comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['id','category','conversation','original_answer','desired_answer','adapter_answer','output_tokens','native_eos','finish_reason']
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader()
        for r in answers:
            writer.writerow({k:( '\n\n'.join(m['role']+': '+m['content'] for m in r['messages']) if k=='conversation' else r[k]) for k in fields})
    manifest.update(status='completed',count=len(answers),native_eos_count=sum(r['native_eos'] for r in answers),
        incomplete_ids=[r['id'] for r in answers if not r['native_eos']],
        files={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in a.output_dir.iterdir() if f.is_file() and f.name!='manifest.json'})
    write_manifest()

if __name__=='__main__':
    main()
