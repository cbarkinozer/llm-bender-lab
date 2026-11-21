"""Merge verified adapters, run matched development inference and package small artifacts."""
import argparse, gc, hashlib, json, os, subprocess, tarfile, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/turkish-capability/lfm3-1.7b'
SESSION=Path('/workspace/lfm3-cookbook')
EXPS=['exp-014-completion-mask','exp-015-cookbook-recipe']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')

def merge(exp):
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from peft import PeftModel
    cfg=read(BASE/exp/'config.json');out=BASE/exp/'results-local';source=out/'sft/adapter';dest=out/'merged-model'
    assert read(out/'sft/training-manifest.json')['status']=='passed'
    assert not dest.exists()
    kw=dict(revision=cfg['model']['revision'],code_revision=cfg['model']['revision'],trust_remote_code=True,dtype=torch.bfloat16)
    tok=AutoTokenizer.from_pretrained(cfg['model']['repo'],revision=cfg['model']['revision'],trust_remote_code=True)
    model=PeftModel.from_pretrained(AutoModelForCausalLM.from_pretrained(cfg['model']['repo'],**kw).to('cuda'),source).eval()
    probe=tok('Merhaba. 2 + 3 =',return_tensors='pt').to('cuda')
    with torch.inference_mode():before=model(**probe,use_cache=False).logits[:,-1].float().cpu()
    model=model.merge_and_unload(safe_merge=True).eval();model.config.use_cache=True
    with torch.inference_mode():merged=model(**probe,use_cache=False).logits[:,-1].float().cpu()
    model.save_pretrained(dest,safe_serialization=True);tok.save_pretrained(dest)
    del model;gc.collect();torch.cuda.empty_cache()
    model=AutoModelForCausalLM.from_pretrained(dest,trust_remote_code=True,dtype=torch.bfloat16).to('cuda').eval()
    with torch.inference_mode():after=model(**probe,use_cache=False).logits[:,-1].float().cpu()
    assert torch.equal(merged,after),'Merged reload parity failed'
    dump(out/'merge-receipt.json',dict(status='passed',reload_exact=True,max_abs_merge_difference=float((before-merged).abs().max()),source_adapter_sha256=sha(source/'adapter_model.safetensors'),merged_files={f.name:sha(f) for f in dest.iterdir() if f.is_file()}))

def infer(exp):
    for thinking,packet in [(False,'prompts.jsonl'),(True,'thinking-prompts.jsonl')]:
        source=BASE/'stage-diagnostic-v01'/packet
        out=(BASE/'cookbook-runtime-local/base' if exp=='base' else BASE/exp/'results-local')/('inference-on' if thinking else 'inference-off')
        cmd=['/workspace/.venvs/lfm3-stage/bin/python',str(ROOT/'scripts/evaluation/evaluate_lfm3_vllm_batched.py'),
             '--experiment-dir',str(BASE/'exp-000-baseline'),'--output-dir',str(out),
             '--packet-path',str(source),'--packet-sha256',sha(source),'--all-rows','--batch-size','4',
             '--temperature','0.1','--top-k','50','--repetition-penalty','1.1',
             '--protocol-name','stage-diagnostic-v01-matched-cookbook']
        if exp!='base':cmd+=['--merged-model',str(BASE/exp/'results-local/merged-model')]
        if thinking:cmd+=['--enable-thinking']
        # Setup script records the exact CUDA library paths needed by this venv.
        import shlex
        shell='source /workspace/lfm3-stage-env.sh; exec '+shlex.join(cmd)
        with (SESSION/f'{exp}-inference-{thinking}.log').open('w') as log:subprocess.run(['bash','-c',shell],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        assert read(out/'manifest.json')['status']=='completed'

def package():
    run=BASE/'cookbook-runtime-local';run.mkdir(exist_ok=True)
    for f in SESSION.glob('*.log'):(run/f.name).write_bytes(f.read_bytes())
    for f in (ROOT/'scripts/training').glob('*lfm3_cookbook*'):(run/f.name).write_bytes(f.read_bytes())
    files=[]
    for folder in [run]+[BASE/e/'results-local' for e in EXPS]:
        files.extend(p for p in folder.rglob('*') if p.is_file() and 'merged-model' not in p.parts and p.name not in ['artifacts.tar.gz','LOCAL-BACKUP-RECEIPT.json'])
    files=sorted(set(files));hashes={str(p.relative_to(ROOT)):sha(p) for p in files}
    with tarfile.open(SESSION/'artifacts.tar.gz','w:gz') as t:
        for p in files:t.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    dump(SESSION/'backup.json',dict(status='packaged',sha256=sha(SESSION/'artifacts.tar.gz'),files=hashes,full_weights_included=False))
    print('PACKAGED',len(files),flush=True)

if __name__=='__main__':
    os.environ.setdefault('HF_HOME','/workspace/.cache/huggingface');os.environ.setdefault('HF_HUB_DISABLE_XET','1')
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['merge','infer','package','session']);p.add_argument('--experiment',default=EXPS[0]);a=p.parse_args()
    if a.mode=='merge':merge(a.experiment)
    elif a.mode=='infer':infer(a.experiment)
    elif a.mode=='package':package()
    else:
        deadline=time.monotonic()+7200
        while not all((BASE/e/'results-local/sft/training-manifest.json').exists() for e in EXPS):
            assert time.monotonic()<deadline,'Training wait timeout'
            assert 'SESSION_FAILED' not in (SESSION/'session.log').read_text(),'Training session failed; inspect logs'
            time.sleep(10)
        for e in EXPS:
            subprocess.run(['/workspace/.venvs/lfm3-cookbook/bin/python',__file__,'merge','--experiment',e],check=True)
            infer(e)
        infer('base');package()
        print('ALL_TRAINING_INFERENCE_PACKAGED',flush=True)
