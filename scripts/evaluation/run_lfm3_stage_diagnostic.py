"""Inference only: exact base -> CPT -> CPT+bilingual69 lineage, two separate modes."""
import argparse
import gc
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/turkish-capability/lfm3-1.7b'
DATA=BASE/'stage-diagnostic-v01'
OUT=BASE/'stage-diagnostic-v01-local'
BASE_REV='0dc4268b561499c648c7ba7c9466bf3d8d01517a'
CPT_REV='6f213ec25a944dab2fbdeb6d337deb0e0442e638'
MODELS=['base','cpt','cpt-bilingual69']

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def rows(p):return [json.loads(l) for l in Path(p).read_text(encoding='utf-8').splitlines()]
def dump(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def verify():
    m=read(DATA/'freeze.json');assert m['training_authorized'] is False
    for name,digest in m['files'].items():assert sha(ROOT/name)==digest,name
    assert len(rows(DATA/'prompts.jsonl'))==72 and len(rows(DATA/'thinking-prompts.jsonl'))==16
    return m

def prepare():
    verify()
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM,GenerationConfig
    from peft import PeftModel
    cache=Path(os.environ['HF_HOME'])/'hub'
    original=cache/'models--LiquidAI--LFM3-1.7B/snapshots'/BASE_REV
    cpt_adapter=cache/'models--cbarkinozer--LFM3-1.7B-Turkish-CPT/snapshots'/CPT_REV
    assert sha(original/'model.safetensors')=='135922caef64e81e52af88ede8b7c3ddaa9d6da220a9737fb3065275dbfb4330'
    assert sha(cpt_adapter/'adapter_model.safetensors')=='363a4caea00bc5af708aada319064f90a3bc31fe2b636d3c741d8a644feebc32'
    tok=AutoTokenizer.from_pretrained(original,trust_remote_code=True)
    assert hashlib.sha256(tok.chat_template.encode()).hexdigest()=='f45005c50cd2a97329722bf3a2dee9f16c04cdf825a589b280fb7e99e6827818'
    eos=GenerationConfig.from_pretrained(original).eos_token_id
    assert (eos if isinstance(eos,list) else [eos])==[124900]
    audits=[]
    for thinking,packet in [(False,'prompts.jsonl'),(True,'thinking-prompts.jsonl')]:
        for r in rows(DATA/packet):
            text=tok.apply_chat_template(r['messages'],tokenize=False,add_generation_prompt=True,enable_thinking=thinking)
            expected='<|startoftext|>'+''.join('<|im_start|>'+m['role']+'\n'+m['content']+'<|im_end|>\n' for m in r['messages'])+'<|im_start|>assistant\n'+('<think>' if thinking else '<think></think>')
            assert text==expected,r['id']
            ids=tok(text,add_special_tokens=False)['input_ids']
            assert ids==tok.apply_chat_template(r['messages'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=thinking)
            assert len(ids)+4096<=8192
            audits.append(dict(id=r['id'],thinking=thinking,prompt_tokens=len(ids),rendered_sha256=hashlib.sha256(text.encode()).hexdigest()))
    dump(OUT/'prompt-audit.json',dict(status='passed',eos=124900,records=audits))
    def merge(source,adapter,dest,expected):
        receipt=OUT/'merge-receipts'/(dest.name+'.json')
        if receipt.exists():assert sha(dest/'model.safetensors')==read(receipt)['weight_sha256'];return
        assert not dest.exists(),'Preserve incomplete merge before retry'
        m=AutoModelForCausalLM.from_pretrained(source,dtype=torch.bfloat16,trust_remote_code=True).to('cuda').eval()
        m=PeftModel.from_pretrained(m,adapter).merge_and_unload(safe_merge=True).eval();m.config.use_cache=True
        probe=tok('Merhaba.',return_tensors='pt').to('cuda')
        with torch.inference_mode():before=m(**probe,use_cache=False).logits[:,-1].cpu()
        m.save_pretrained(dest,safe_serialization=True);tok.save_pretrained(dest)
        del m;gc.collect();torch.cuda.empty_cache()
        m=AutoModelForCausalLM.from_pretrained(dest,dtype=torch.bfloat16,trust_remote_code=True).to('cuda').eval()
        with torch.inference_mode():after=m(**probe,use_cache=False).logits[:,-1].cpu()
        assert torch.equal(before,after) and sha(dest/'model.safetensors')==expected
        dump(receipt,dict(status='passed',reload_exact=True,weight_sha256=expected,adapter_sha256=sha(adapter/'adapter_model.safetensors')))
        del m;gc.collect();torch.cuda.empty_cache()
    cpt=OUT/'models/cpt'
    merge(original,cpt_adapter,cpt,'f4562118c3196462d73649198d856450714ae67081cd6af7df851f59dccf5e46')
    merge(cpt,BASE/'exp-011-bilingual-sft640/results-local/sft/checkpoint-69',OUT/'models/cpt-bilingual69',
          '23f204c8309efded7ead27e2b89ee0ea17c8a3adcd3e007b6ca1075934f00682')
    dump(OUT/'environment.json',dict(packages={p:importlib.metadata.version(p) for p in ['torch','transformers','vllm','peft','tokenizers','jinja2']},
        python=sys.version,gpu=torch.cuda.get_device_name(),cuda=torch.version.cuda,tf32=torch.backends.cuda.matmul.allow_tf32,
        source_freeze_sha256=sha(DATA/'freeze.json')))

def evaluate(label,packet,cohort,thinking=False):
    dest=OUT/'inference'/cohort/label;expected=len(rows(packet))
    if (dest/'manifest.json').exists():
        m=read(dest/'manifest.json')
        assert m['status']=='completed' and m['count']==expected and m['questions_sha256']==sha(packet)
        assert m['decoding']['enable_thinking']==thinking
        actual=rows(dest/'answers.jsonl');assert len(actual)==expected and {r['id'] for r in actual}=={r['id'] for r in rows(packet)}
        return
    assert not dest.exists(),'Interrupted run preserved; inspect rather than overwrite'
    cmd=[sys.executable,ROOT/'scripts/evaluation/evaluate_lfm3_vllm_batched.py','--experiment-dir',BASE/'exp-000-baseline',
        '--output-dir',dest,'--batch-size','4','--temperature','0.1','--top-k','50','--repetition-penalty','1.1',
        '--packet-path',packet,'--packet-sha256',sha(packet),'--all-rows','--protocol-name','stage-diagnostic-v01-'+cohort]
    if label!='base':cmd+=['--merged-model',OUT/'models'/label]
    if thinking:cmd+=['--enable-thinking']
    log=OUT/'logs'/f'{cohort}-{label}.log';log.parent.mkdir(parents=True,exist_ok=True)
    print('START',cohort,label,flush=True)
    with log.open('xb') as f:subprocess.run(list(map(str,cmd)),cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
    m=read(dest/'manifest.json');actual=rows(dest/'answers.jsonl')
    assert m['status']=='completed' and m['count']==len(actual)==expected
    assert all(r['generated_tokens']>0 and r['raw_output'].strip() for r in actual)
    print('DONE',cohort,label,flush=True)

def run():
    verify();assert read(OUT/'prompt-audit.json')['status']=='passed'
    smoke=OUT/'smoke-prompts.jsonl'
    if not smoke.exists():smoke.parent.mkdir(parents=True,exist_ok=True);smoke.write_text(''.join(json.dumps(r)+'\n' for r in [
        dict(id='smoke-en',messages=[dict(role='user',content='Name one color. Answer in English with one word.')]),
        dict(id='smoke-tr',messages=[dict(role='user',content='Bir hayvan ismi yaz. Tek kelime kullan.')])]),encoding='utf-8')
    evaluate('base',smoke,'non-test-smoke')
    assert all(r['finish_reason']=='eos' for r in rows(OUT/'inference/non-test-smoke/base/answers.jsonl'))
    for label in MODELS:evaluate(label,DATA/'prompts.jsonl','main-off')
    for label in MODELS:evaluate(label,DATA/'thinking-prompts.jsonl','thinking-on',True)
    dump(OUT/'completion.json',dict(status='completed',outputs=264,smoke_outputs=2,training_performed=False,models=MODELS))

def package():
    verify();assert read(OUT/'completion.json')['status']=='completed'
    files=[p for p in OUT.rglob('*') if p.is_file() and 'models' not in p.relative_to(OUT).parts and p.suffix!='.gz' and p.name!='backup-manifest.json']
    dump(OUT/'backup-manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in files})
    archive=Path('/workspace/stage-diagnostic-artifacts.tar.gz')
    with tarfile.open(archive,'w:gz') as t:
        for p in files+[OUT/'backup-manifest.json']:t.add(p,arcname=p.relative_to(ROOT))
    print(json.dumps(dict(path=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,files=len(files),contains_full_weights=False)))

if __name__=='__main__':
    os.environ.setdefault('HF_HOME','/workspace/.cache/huggingface')
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['verify','prepare','run','package']);a=p.parse_args()
    globals()[a.phase]()
