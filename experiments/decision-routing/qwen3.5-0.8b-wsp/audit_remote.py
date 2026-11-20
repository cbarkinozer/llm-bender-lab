import os,json,hashlib,sys
from pathlib import Path
os.environ['NLTK_DATA']='/root/nltk_data'
from run_card_eval import grade
root=Path('/workspace/reflex-wsp')
for line in (root/'bench/ifeval.jsonl').read_text().splitlines():
    r=json.loads(line);grade(r,'</think> This is a sample answer. It has two sentences.')
print('All 541 IFEval records constructed and graded',flush=True)
from safetensors import safe_open
import torch
models=json.loads((root/'models.json').read_text())
def tensors(path):
    result={}
    for p in Path(path).glob('*.safetensors'):
        with safe_open(p,framework='pt',device='cpu') as f:
            for key in f.keys():result[key]=f.get_tensor(key)
    return result
parent=tensors(models['parent']);wsp=tensors(models['wsp']);report={'parent_keys':len(parent),'wsp_keys':len(wsp),'keys_parent_only':sorted(parent.keys()-wsp.keys()),'keys_wsp_only':sorted(wsp.keys()-parent.keys()),'changed':[]}
for k in sorted(parent.keys()&wsp.keys()):
    a,b=parent[k],wsp[k]
    if not torch.equal(a,b):
        report['changed'].append({'key':k,'shape':list(b.shape),'dtype':str(b.dtype),'different_elements':int((a!=b).sum()),'wsp_sha256':hashlib.sha256(b.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()})
(root/'weight-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)