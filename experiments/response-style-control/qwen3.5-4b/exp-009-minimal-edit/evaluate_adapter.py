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

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--adapter',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args()
    if a.output_dir.exists():
        raise ValueError('Refusing overwrite')
    from unsloth import FastLanguageModel
    from peft import PeftModel
    import torch
    from transformers import AutoTokenizer, set_seed
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
    manifest=dict(status='running',model='unsloth/Qwen3.5-4B',revision=REV,adapter=str(a.adapter),
        adapter_hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in a.adapter.glob('*') if f.is_file()},
        validation_sha256=expected,ids=[r['id'] for r in rows],seed=3407,
        generation=dict(do_sample=False,num_beams=1,repetition_penalty=1.05,budgets=[4096,8192,16384],thinking=False,additional_system_prompt=None),
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
    with (a.output_dir/'attempts.jsonl').open('w',encoding='utf-8') as attempts, (a.output_dir/'answers.jsonl').open('w',encoding='utf-8') as output:
        for r in rows:
            ids=tok.apply_chat_template(r['messages'],tokenize=True,add_generation_prompt=True,enable_thinking=False)
            x=torch.tensor([ids],device=next(model.parameters()).device)
            complete=False
            for budget in [4096,8192,16384]:
                started=time.time()
                with torch.inference_mode():
                    y=model.generate(input_ids=x,attention_mask=torch.ones_like(x),do_sample=False,num_beams=1,
                        repetition_penalty=1.05,max_new_tokens=budget,eos_token_id=eos,pad_token_id=tok.pad_token_id,
                        forced_eos_token_id=None,use_cache=True)
                tokens=y[0,len(ids):].tolist()
                complete=bool(tokens and tokens[-1] in eos)
                answer=tok.decode(tokens,skip_special_tokens=True)
                result=dict(id=r['id'],category=r['category'],messages=r['messages'],original_answer=r['original_answer'],
                    desired_answer=r['desired_answer'],adapter_answer=answer,prompt_token_ids=ids,output_token_ids=tokens,
                    output_tokens=len(tokens),budget=budget,native_eos=complete,seconds=time.time()-started)
                attempts.write(json.dumps(result,ensure_ascii=False)+'\n'); attempts.flush()
                del y
                if complete:
                    break
            output.write(json.dumps(result,ensure_ascii=False)+'\n'); output.flush()
            answers.append(result)
            print(r['id'],len(tokens),'EOS' if complete else 'LENGTH_LIMIT',flush=True)
    with (a.output_dir/'comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['id','category','conversation','original_answer','desired_answer','adapter_answer','output_tokens','native_eos']
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader()
        for r in answers:
            writer.writerow({k:( '\n\n'.join(m['role']+': '+m['content'] for m in r['messages']) if k=='conversation' else r[k]) for k in fields})
    manifest.update(status='completed',count=len(answers),native_eos_count=sum(r['native_eos'] for r in answers),
        files={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in a.output_dir.iterdir() if f.is_file() and f.name!='manifest.json'})
    write_manifest()

if __name__=='__main__':
    main()
