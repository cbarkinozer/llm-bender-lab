import os,json,urllib.request,hashlib
from pathlib import Path
os.environ['HF_HOME']='/workspace/.cache/huggingface'
from huggingface_hub import HfApi,snapshot_download
from datasets import load_dataset
root=Path('/workspace/reflex-wsp'); bench=root/'bench'; bench.mkdir(exist_ok=True)
a=HfApi(); manifest={}
for name,repo,config,split in [('math500','HuggingFaceH4/MATH-500',None,'test'),('gsm8k','openai/gsm8k','main','test'),('ifeval','google/IFEval',None,'train')]:
    rev=a.dataset_info(repo).sha
    ds=load_dataset(repo,config,split=split,revision=rev)
    rows=[]
    for i,r in enumerate(ds):
        if name=='math500': row={'id':r['unique_id'],'problem':r['problem'],'answer':r['answer']}
        elif name=='gsm8k': row={'id':f'gsm8k_test_{i}','problem':r['question'],'answer':r['answer'].split('####')[-1].strip().replace(',','')}
        else: row={**dict(r),'id':str(r['key']),'kind':'ifeval'}
        rows.append(row)
    p=bench/f'{name}.jsonl'; p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
    manifest[name]={'repo':repo,'revision':rev,'config':config,'split':split,'rows':len(rows),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    (bench/'manifest.json').write_text(json.dumps(manifest,indent=2)); print(name,manifest[name],flush=True)
commit='c878a53ec1764bcb91a6178dc5c315202a3b5fa2'
pkg=root/'tools'/'instruction_following_eval';pkg.mkdir(exist_ok=True); (pkg/'__init__.py').touch()
for f in ['instructions.py','instructions_registry.py','instructions_util.py']:
    urllib.request.urlretrieve(f'https://raw.githubusercontent.com/google-research/google-research/{commit}/instruction_following_eval/{f}',pkg/f)
print('IFEval code',commit,flush=True)
models={}
for name,repo,rev in [('wsp','RikiyaT/Qwen3.5-0.8B-weight-space-programming','d1671a178705bcab7644806d23c535517f35723b'),('parent','Qwen/Qwen3.5-0.8B','2fc06364715b967f1860aea9cf38778875588b17')]:
    models[name]=snapshot_download(repo,revision=rev,ignore_patterns=['*.gguf','*.onnx','*.bin'])
    (root/'models.json').write_text(json.dumps(models,indent=2));print(name,models[name],flush=True)