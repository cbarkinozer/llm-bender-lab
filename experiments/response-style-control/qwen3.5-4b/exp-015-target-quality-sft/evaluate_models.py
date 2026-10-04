"""Canonical base/C/E/F generation; controls are read only for inference."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
REV = '3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def rows():
    sources = [HERE/'data-reviewed-v1/validation-reviewed.jsonl', HERE/'controls-reviewed-v1/questions-12.jsonl']
    data = [json.loads(line) for p in sources for line in p.read_text(encoding='utf-8').splitlines()]
    assert len(data)==32 and len({r['id'] for r in data})==32
    assert all(r['evaluation_only'] and r['split'] in ('validation','control') for r in data)
    return data, {str(p.relative_to(HERE)):digest(p) for p in sources}

def repeated_tail(tokens):
    for width in range(32, min(512,len(tokens)//4)+1):
        if tokens[-width:]*4==tokens[-4*width:]:
            return width
    return None

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--adapter',type=Path)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--reload-check',type=Path,help='Diagnostic tokenized TRAIN rows only; no benchmark inference')
    a=p.parse_args()
    assert not a.output_dir.exists(), 'Refusing overwrite'
    from unsloth import FastLanguageModel
    import torch
    from peft import PeftModel
    from transformers import AutoTokenizer, StoppingCriteria, StoppingCriteriaList, set_seed
    set_seed(3407)
    model,_=FastLanguageModel.from_pretrained(model_name='unsloth/Qwen3.5-4B',revision=REV,
        max_seq_length=32768,load_in_4bit=False,load_in_16bit=True,full_finetuning=False)
    if a.adapter:
        model=PeftModel.from_pretrained(model,str(a.adapter),is_trainable=False)
        assert any('lora_' in n for n,_ in model.named_parameters())
    FastLanguageModel.for_inference(model)
    model.eval()
    tok=AutoTokenizer.from_pretrained('unsloth/Qwen3.5-4B',revision=REV)
    a.output_dir.mkdir(parents=True)
    if a.reload_check:
        assert a.adapter and a.reload_check.name=='train-tokenized.jsonl'
        example=json.loads(a.reload_check.read_text().splitlines()[0])
        batch={k:torch.tensor([example[k]],device=next(model.parameters()).device) for k in ('input_ids','attention_mask','labels')}
        with torch.inference_mode():
            loss=model(**batch).loss.item()
        assert torch.isfinite(torch.tensor(loss))
        write(a.output_dir/'result.json',dict(status='passed',adapter_save_reload=True,loss=loss,
            adapter_hashes={f.name:digest(f) for f in a.adapter.iterdir() if f.is_file()},train_source_sha256=digest(a.reload_check)))
        return
    data,hashes=rows()
    eos=model.generation_config.eos_token_id
    eos=[eos] if isinstance(eos,int) else eos
    assert eos
    manifest=dict(status='running',count=0,model='unsloth/Qwen3.5-4B',revision=REV,adapter=str(a.adapter) if a.adapter else None,
        adapter_hashes={f.name:digest(f) for f in a.adapter.iterdir() if f.is_file()} if a.adapter else {},sources=hashes,
        ids=[r['id'] for r in data],backend='Unsloth/Transformers',precision='BF16',batch_size=1,seed=3407,
        generation=dict(do_sample=False,num_beams=1,repetition_penalty=1.05,max_new_tokens=4096,thinking=False,
            additional_system_prompt=None,guard='180 seconds or exact 32..512-token period repeated four times; non-EOS failure'),
        packages={n:importlib.metadata.version(n) for n in ('torch','transformers','unsloth','peft')},
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip(),
        chat_template_sha256=hashlib.sha256(tok.chat_template.encode()).hexdigest(),eos_token_ids=eos)
    write(a.output_dir/'manifest.json',manifest)
    (a.output_dir/'chat_template.jinja').write_text(tok.chat_template,encoding='utf-8')
    results=[]
    with (a.output_dir/'answers.jsonl').open('x',encoding='utf-8') as out:
        for row in data:
            ids=tok.apply_chat_template(row['messages'],tokenize=True,add_generation_prompt=True,enable_thinking=False)
            rendered=tok.apply_chat_template(row['messages'],tokenize=False,add_generation_prompt=True,enable_thinking=False)
            x=torch.tensor([ids],device=next(model.parameters()).device)
            started=time.monotonic()
            class Guard(StoppingCriteria):
                reason=None
                def __call__(self,input_ids,scores,**kwargs):
                    count=input_ids.shape[1]-len(ids)
                    if count%16==0 and repeated_tail(input_ids[0,len(ids):].tolist()):
                        self.reason='repetition_guard'
                    if time.monotonic()-started>180:
                        self.reason=self.reason or 'wall_time_guard'
                    if count%128==0:
                        write(a.output_dir/'progress.json',dict(id=row['id'],output_tokens=count,seconds=time.monotonic()-started))
                    return self.reason is not None
            guard=Guard()
            with torch.inference_mode():
                y=model.generate(input_ids=x,attention_mask=torch.ones_like(x),do_sample=False,num_beams=1,
                    repetition_penalty=1.05,max_new_tokens=4096,eos_token_id=eos,pad_token_id=tok.pad_token_id,
                    forced_eos_token_id=None,use_cache=True,stopping_criteria=StoppingCriteriaList([guard]))
            tokens=y[0,len(ids):].tolist()
            complete=bool(tokens and tokens[-1] in eos)
            result=dict(id=row['id'],category=row['category'],split=row['split'],skill=row.get('skill'),
                messages=row['messages'],desired_answer=row['desired_answer'],answer=tok.decode(tokens,skip_special_tokens=True),
                rendered_prompt=rendered,prompt_token_ids=ids,output_token_ids=tokens,output_tokens=len(tokens),native_eos=complete,
                seconds=time.monotonic()-started,finish_reason='native_eos' if complete else guard.reason or 'length_limit')
            out.write(json.dumps(result,ensure_ascii=False)+'\n'); out.flush()
            results.append(result)
            print(row['id'],len(tokens),result['finish_reason'],flush=True)
            del y,x
    manifest.update(status='completed',count=len(results),native_eos_count=sum(r['native_eos'] for r in results),
        incomplete_ids=[r['id'] for r in results if not r['native_eos']],answers_sha256=digest(a.output_dir/'answers.jsonl'))
    write(a.output_dir/'manifest.json',manifest)

if __name__=='__main__':
    main()
