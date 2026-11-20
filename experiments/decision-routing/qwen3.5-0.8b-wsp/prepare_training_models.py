import os,json,hashlib
from pathlib import Path
os.environ['HF_HOME']='/workspace/.cache/huggingface'
from huggingface_hub import snapshot_download
root=Path('/workspace/reflex-wsp');models=json.loads((root/'models.json').read_text())
for name,repo,rev in [('original_training_base','unsloth/Qwen3.5-0.8B','23c69c53358a07516b5827588b3fdb12ae78fd65'),('released_reflex','cbarkinozer/Reflex-1','252a00c22cebca07c7ff4d6f99be15863c7faab2')]:
    models[name]=snapshot_download(repo,revision=rev,ignore_patterns=['*.gguf','*.onnx','*.bin'])
    (root/'models.json').write_text(json.dumps(models,indent=2));print(name,models[name],flush=True)
from safetensors import safe_open
import torch
def tensors(path):
    result={}
    for p in Path(path).glob('*.safetensors'):
        with safe_open(p,framework='pt',device='cpu') as f:
            for key in f.keys():result[key]=f.get_tensor(key)
    return result
p=tensors(models['parent']);u=tensors(models['original_training_base'])
report={'parent_keys':len(p),'unsloth_keys':len(u),'parent_only':sorted(p.keys()-u.keys()),'unsloth_only':sorted(u.keys()-p.keys()),'changed':[k for k in sorted(p.keys()&u.keys()) if not torch.equal(p[k],u[k])]}
(root/'unsloth-parent-audit.json').write_text(json.dumps(report,indent=2));print(report,flush=True)