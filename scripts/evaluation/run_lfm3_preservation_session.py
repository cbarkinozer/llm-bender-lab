"""Versioned three-experiment session; frozen inputs, explicit model lineage, raw outputs."""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/turkish-capability/lfm3-1.7b'
RUN=BASE/'preservation-session-v01-local'
DATA=BASE/'capability-preservation-v01'
BASE_REV='0dc4268b561499c648c7ba7c9466bf3d8d01517a'
CPT_REV='6f213ec25a944dab2fbdeb6d337deb0e0442e638'
EXPERIMENTS=['exp-012-base-bilingual','exp-013-base-preservation']
OLD=[('turkish60','exp-010-tr-only-sft160',60),('bilingual69','exp-011-bilingual-sft640',69)]

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def verify():
    m=read(RUN/'freeze.json')
    for name,digest in m['files'].items():assert sha(ROOT/name)==digest,name
    return m

def prepare():
    verify()
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from peft import PeftModel
    cache=Path(os.environ['HF_HOME'])/'hub'
    original=cache/'models--LiquidAI--LFM3-1.7B/snapshots'/BASE_REV
    cpt_adapter=cache/'models--cbarkinozer--LFM3-1.7B-Turkish-CPT/snapshots'/CPT_REV
    assert (original/'model.safetensors').exists() and (cpt_adapter/'adapter_model.safetensors').exists()
    tok=AutoTokenizer.from_pretrained(original,trust_remote_code=True)
    assert hashlib.sha256(tok.chat_template.encode()).hexdigest()=='f45005c50cd2a97329722bf3a2dee9f16c04cdf825a589b280fb7e99e6827818'
    parent=RUN/'parent-prepare';parent.mkdir(parents=True,exist_ok=True)
    link=parent/'cpt-merged'
    # Historical trainer's directory name is legacy; BOTH NEW runs use original base.
    if not link.exists():link.symlink_to(original,target_is_directory=True)
    assert link.resolve()==original.resolve()
    assert sha(original/'model.safetensors')=='135922caef64e81e52af88ede8b7c3ddaa9d6da220a9737fb3065275dbfb4330'
    dump(parent/'cpt-merge.json',dict(actual_parent='original-base-NOT-CPT',revision=BASE_REV,
        weight_sha256=sha(original/'model.safetensors'),path=str(original),legacy_path_name_only=True))
    def merge(source,adapter,dest,expected=None):
        receipt=dest/'merge-receipt.json'
        if receipt.exists():
            assert sha(dest/'model.safetensors')==read(receipt)['weight_sha256'];return
        assert not dest.exists(),'Preserve interrupted merge for diagnosis'
        m=AutoModelForCausalLM.from_pretrained(source,dtype=torch.bfloat16,trust_remote_code=True).to('cuda').eval()
        m=PeftModel.from_pretrained(m,adapter).merge_and_unload(safe_merge=True).eval();m.config.use_cache=True
        probe=tok('Merhaba.',return_tensors='pt').to('cuda')
        with torch.inference_mode():before=m(**probe,use_cache=False).logits[:,-1].cpu()
        m.save_pretrained(dest,safe_serialization=True);tok.save_pretrained(dest)
        del m;gc.collect();torch.cuda.empty_cache()
        m=AutoModelForCausalLM.from_pretrained(dest,dtype=torch.bfloat16,trust_remote_code=True).to('cuda').eval()
        with torch.inference_mode():after=m(**probe,use_cache=False).logits[:,-1].cpu()
        assert torch.equal(before,after)
        digest=sha(dest/'model.safetensors')
        if expected:assert digest==expected,(dest,digest)
        result=dict(status='passed',reload_exact=True,weight_sha256=digest,adapter_sha256=sha(Path(adapter)/'adapter_model.safetensors'))
        dump(receipt,result);dump(RUN/'merge-receipts'/(dest.name+'.json'),result)
        del m;gc.collect();torch.cuda.empty_cache()
    cpt=RUN/'models/cpt'
    merge(original,cpt_adapter,cpt,'f4562118c3196462d73649198d856450714ae67081cd6af7df851f59dccf5e46')
    for label,exp,step in OLD:
        expected={'turkish60':'6ecc1e57c9fe45d718357435328a889222247c353f574144a92c76f767b27cd5',
                  'bilingual69':'23f204c8309efded7ead27e2b89ee0ea17c8a3adcd3e007b6ca1075934f00682'}[label]
        merge(cpt,BASE/exp/'results-local/sft'/f'checkpoint-{step}',RUN/'models'/label,expected)
    for exp in EXPERIMENTS:
        adapter=BASE/exp/'results-local/sft/checkpoint-69'
        if adapter.exists():merge(original,adapter,RUN/'models'/exp)
    dump(RUN/'parent-ready.json',dict(status='passed',actual_training_parent='original-base',revision=BASE_REV))

def evaluate(label,packet,thinking=False,cohort='fresh'):
    dest=RUN/'inference'/cohort/label
    if (dest/'manifest.json').exists():
        m=read(dest/'manifest.json');assert m['status']=='completed';return
    cmd=[sys.executable,ROOT/'scripts/evaluation/evaluate_lfm3_vllm_batched.py',
         '--experiment-dir',BASE/'exp-000-baseline','--output-dir',dest,'--batch-size','4',
         '--temperature','0.1','--top-k','50','--repetition-penalty','1.1',
         '--protocol-name','preservation-v01-'+cohort+('-thinking-on' if thinking else '-thinking-off'),
         '--packet-path',packet,'--packet-sha256',sha(packet),'--all-rows']
    if label!='base':cmd+=['--merged-model',RUN/'models'/label]
    if thinking:cmd+=['--enable-thinking']
    log=RUN/'logs'/f'eval-{cohort}-{label}.log';log.parent.mkdir(parents=True,exist_ok=True)
    print('START',cohort,label,flush=True)
    with log.open('xb') as f:subprocess.run(list(map(str,cmd)),cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
    print('DONE',cohort,label,flush=True)

def baseline():
    verify()
    for label in ['base','turkish60','bilingual69']:evaluate(label,DATA/'eval-prompts.jsonl')
    dump(RUN/'baseline-completion.json',dict(status='completed',labels=['base','turkish60','bilingual69']))

def thinking():
    verify()
    for label in ['base','turkish60','bilingual69']:evaluate(label,RUN/'thinking-prompts.jsonl',True,'thinking-diagnostic')
    dump(RUN/'thinking-completion.json',dict(status='completed',note='Consumed test diagnostic, not fresh final evaluation'))

def candidates():
    verify()
    for label in EXPERIMENTS:evaluate(label,DATA/'eval-prompts.jsonl')
    for label in EXPERIMENTS:
        evaluate(label,RUN/'symbolic-prompts.jsonl',False,'new-symbolic-off')
        evaluate(label,RUN/'symbolic-prompts.jsonl',True,'new-symbolic-on')
    dump(RUN/'completion.json',dict(status='completed',new_training_runs=2,primary_checkpoint=69))

def package():
    assert read(RUN/'completion.json')['status']=='completed'
    files=[p for p in RUN.rglob('*') if p.is_file() and 'models' not in p.relative_to(RUN).parts
           and 'parent-prepare' not in p.relative_to(RUN).parts and p.suffix!='.gz' and p.name!='backup-manifest.json']
    # Primary and late adapters only; no base/merged weights or optimizer tensors.
    for exp in EXPERIMENTS:
        out=BASE/exp/'results-local'
        for p in out.rglob('*'):
            if not p.is_file():continue
            if p.suffix in ['.json','.jsonl','.txt','.yaml'] or (p.name=='adapter_model.safetensors' and p.parent.name in ['checkpoint-69','checkpoint-113']):files.append(p)
    files+=list(Path('/workspace/setup-logs').glob('*.log'))+list(Path('/workspace/setup-logs').glob('*freeze.txt'))
    files=list(dict.fromkeys(files))
    dump(RUN/'backup-manifest.json',{str(p.relative_to('/workspace')):sha(p) for p in files})
    archive=Path('/workspace/preservation-artifacts.tar.gz')
    with tarfile.open(archive,'w:gz') as t:
        for p in files+[RUN/'backup-manifest.json']:t.add(p,arcname=p.relative_to('/workspace'))
    print(json.dumps(dict(path=str(archive),sha256=sha(archive),files=len(files),bytes=archive.stat().st_size)),flush=True)

if __name__=='__main__':
    os.environ.setdefault('HF_HOME','/workspace/.cache/huggingface')
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','baseline','thinking','candidates','package']);a=p.parse_args()
    globals()[a.phase]()
