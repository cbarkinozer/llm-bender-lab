"""Frozen three-candidate inference only; references never enter the pod bundle."""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'experiments/turkish-capability/lfm3-1.7b'
OUT = BASE/'final-eval-v01-local'
PACKET = BASE/'bilingual-pilot-v01/eval-v01'
BASE_REV = '0dc4268b561499c648c7ba7c9466bf3d8d01517a'
CPT_REV = '6f213ec25a944dab2fbdeb6d337deb0e0442e638'
CANDIDATES = [('turkish60','exp-010-tr-only-sft160',60),('bilingual69','exp-011-bilingual-sft640',69)]


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()


def read(p):return json.loads(p.read_text(encoding='utf-8'))


def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def freeze():
    assert not OUT.exists(), 'Existing freeze must not be overwritten'
    files = [Path(__file__), ROOT/'scripts/evaluation/evaluate_lfm3_vllm_batched.py',
        BASE/'exp-000-baseline/config-planned.json',PACKET/'manifest.json',
        PACKET/'eval-prompts.jsonl',PACKET/'symbolic-controls-prompts.jsonl',
        BASE/'bilingual-runtime-local/parent-prepare/cpt-merge.json']
    adapters = {}
    for label,exp,step in CANDIDATES:
        d = BASE/exp/'results-local/sft'/f'checkpoint-{step}'
        files += [d/'adapter_model.safetensors',d/'adapter_config.json']
        adapters[label] = dict(experiment=exp,step=step,sha256=sha(d/'adapter_model.safetensors'))
    assert sha(PACKET/'manifest.json')=='9143d4875329b4577e14d9c2e2cf52747abf572d5bd553947406c4f59da3f556'
    manifest = dict(status='frozen-before-final-inference',base_revision=BASE_REV,cpt_revision=CPT_REV,
        candidates=['base','turkish60','bilingual69'],adapters=adapters,
        decoding=dict(temperature=.1,top_k=50,top_p=1.,repetition_penalty=1.1,max_new_tokens=4096,
            context_budget=8192,enable_thinking=False,ignore_eos=True,stop_token_ids=[124900]),
        seed=3407,batch_size=4,expected_prompts_per_model=148,
        protocol='bilingual-final-v01-thinking-off',training_authorized=False,
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        files={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in files})
    dump(OUT/'freeze.json',manifest)
    with tarfile.open(OUT/'pod-input.tar.gz','w:gz') as t:
        for p in files:t.add(p,arcname=p.relative_to(ROOT))
        t.add(OUT/'freeze.json',arcname=(OUT/'freeze.json').relative_to(ROOT))
    print(json.dumps(dict(freeze_sha256=sha(OUT/'freeze.json'),bundle_sha256=sha(OUT/'pod-input.tar.gz'),adapters=adapters),indent=2))


def verify():
    m = read(OUT/'freeze.json')
    for name,digest in m['files'].items():assert sha(ROOT/name)==digest,name
    return m


def prepare():
    verify()
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from huggingface_hub import snapshot_download
    from peft import PeftModel
    tok = AutoTokenizer.from_pretrained('LiquidAI/LFM3-1.7B',revision=BASE_REV,trust_remote_code=True)
    assert hashlib.sha256(tok.chat_template.encode()).hexdigest()=='f45005c50cd2a97329722bf3a2dee9f16c04cdf825a589b280fb7e99e6827818'
    messages=[dict(role='user',content='Compute 7 + 5. Answer briefly.')]
    rendered=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    ids=tok(rendered,add_special_tokens=False)['input_ids']
    assert ids==tok.apply_chat_template(messages,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
    dump(OUT/'prompt-audit.json',dict(status='passed',rendered_prompt=rendered,prompt_token_ids=ids,
        note='Historical thinking-disabled native prefix preserved unchanged; no output rewriting.',
        native_think_ids=tok.encode('<think></think>',add_special_tokens=False)))
    def merge(model,adapter,dest,expected=None):
        receipt=dest/'merge-receipt.json'
        if receipt.exists():
            assert sha(dest/'model.safetensors')==read(receipt)['weight_sha256']
            return
        assert not dest.exists(),'Inspect incomplete merge before retry'
        m=AutoModelForCausalLM.from_pretrained(model,revision=BASE_REV if model=='LiquidAI/LFM3-1.7B' else None,
            dtype=torch.bfloat16,trust_remote_code=True).to('cuda').eval()
        m=PeftModel.from_pretrained(m,adapter).merge_and_unload(safe_merge=True).eval()
        m.config.use_cache=True
        probe=tok('Merhaba.',return_tensors='pt').to('cuda')
        with torch.inference_mode():before=m(**probe,use_cache=False).logits[:,-1].cpu()
        m.save_pretrained(dest,safe_serialization=True);tok.save_pretrained(dest)
        del m;gc.collect();torch.cuda.empty_cache()
        m=AutoModelForCausalLM.from_pretrained(dest,dtype=torch.bfloat16,trust_remote_code=True).to('cuda').eval()
        with torch.inference_mode():after=m(**probe,use_cache=False).logits[:,-1].cpu()
        assert torch.equal(before,after),'Merge reload mismatch'
        digest=sha(dest/'model.safetensors')
        if expected:assert digest==expected,'CPT parent bytes differ from training parent'
        dump(receipt,dict(status='passed',reload_exact=True,weight_sha256=digest))
        del m;gc.collect();torch.cuda.empty_cache()
    parent=OUT/'models/cpt'
    cpt=snapshot_download('cbarkinozer/LFM3-1.7B-Turkish-CPT',revision=CPT_REV)
    merge('LiquidAI/LFM3-1.7B',cpt,parent,read(BASE/'bilingual-runtime-local/parent-prepare/cpt-merge.json')['files']['model.safetensors'])
    for label,exp,step in CANDIDATES:
        merge(parent,BASE/exp/'results-local/sft'/f'checkpoint-{step}',OUT/'models'/label)


def run():
    manifest=verify()
    rows=[]
    for name in ['eval-prompts.jsonl','symbolic-controls-prompts.jsonl']:
        rows += [json.loads(l) for l in (PACKET/name).read_text(encoding='utf-8').splitlines()]
    assert len(rows)==len({r['id'] for r in rows})==148
    packet=OUT/'questions.jsonl'
    text=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows)
    if packet.exists():assert packet.read_text(encoding='utf-8')==text
    else:packet.write_text(text,encoding='utf-8')
    for label in manifest['candidates']:
        dest=OUT/'inference'/label
        if (dest/'manifest.json').exists():
            old=read(dest/'manifest.json')
            assert old['status']=='completed' and old['count']==148,'Inspect interrupted run; never silently overwrite'
            continue
        cmd=[sys.executable,ROOT/'scripts/evaluation/evaluate_lfm3_vllm_batched.py',
            '--experiment-dir',BASE/'exp-000-baseline','--output-dir',dest,'--batch-size','4',
            '--temperature','0.1','--top-k','50','--repetition-penalty','1.1',
            '--protocol-name',manifest['protocol'],'--packet-path',packet,'--packet-sha256',sha(packet),'--all-rows']
        if label!='base':cmd+=['--merged-model',OUT/'models'/label]
        log=OUT/'logs'/f'{label}.log';log.parent.mkdir(parents=True,exist_ok=True)
        print('START '+label,flush=True)
        with log.open('xb') as f:subprocess.run(list(map(str,cmd)),cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
        assert read(dest/'manifest.json')['count']==148
        print('DONE '+label,flush=True)
    dump(OUT/'completion.json',dict(status='completed',models=3,outputs=444,training_performed=False))


def package():
    assert read(OUT/'completion.json')['status']=='completed'
    files=[p for p in OUT.rglob('*') if p.is_file() and not any(x in p.relative_to(OUT).parts for x in ['models'])
        and p.suffix not in ['.gz'] and p.name!='backup-manifest.json']
    files+=list(Path('/workspace/setup-logs').glob('*'))
    dump(OUT/'backup-manifest.json',{str(p.relative_to('/workspace')):sha(p) for p in files})
    with tarfile.open('/workspace/final-inference-artifacts.tar.gz','w:gz') as t:
        for p in files+[OUT/'backup-manifest.json']:t.add(p,arcname=p.relative_to('/workspace'))
    print(sha(Path('/workspace/final-inference-artifacts.tar.gz')),flush=True)


if __name__=='__main__':
    os.environ.setdefault('HF_HOME','/workspace/.cache/huggingface')
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['freeze','prepare','run','package']);a=p.parse_args()
    globals()[a.phase]()
