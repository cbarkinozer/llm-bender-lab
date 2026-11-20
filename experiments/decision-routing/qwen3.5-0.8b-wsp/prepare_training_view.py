"""Use recovered training metadata with WSP weights, in an isolated symlink view."""
import json,hashlib
from pathlib import Path
root=Path('/workspace/reflex-wsp');models=json.loads((root/'models.json').read_text())
original=Path(models['original_training_base']);wsp=Path(models['wsp']);dest=root/'training-models/wsp-original-metadata';dest.mkdir(parents=True,exist_ok=True)
manifest={'purpose':'Only swap starting weights; preserve recovered Unsloth config/tokenizer for matched training','weight_source':models['wsp'],'metadata_source':models['original_training_base'],'files':{}}
for p in original.iterdir():
    if not p.is_file():continue
    source=wsp/p.name if p.name.endswith('.safetensors') or p.name.endswith('.safetensors.index.json') else p
    if not source.exists():raise FileNotFoundError(source)
    target=dest/p.name
    if target.is_symlink():assert target.resolve()==source.resolve()
    elif target.exists():raise RuntimeError(f'Existing non-symlink {target}')
    else:target.symlink_to(source.resolve())
    manifest['files'][p.name]={'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
(root/'training-view-manifest.json').write_text(json.dumps(manifest,indent=2));models['wsp_training']=str(dest);(root/'models.json').write_text(json.dumps(models,indent=2));print('Prepared',dest,flush=True)