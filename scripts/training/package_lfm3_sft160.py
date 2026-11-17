"""Create a portable LF-normalized pod source/data bundle, excluding credentials."""
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/turkish-capability/lfm3-1.7b'
DEST=BASE/'preparation-local'


def main():
    files=set()
    needed={
        'training':['run_lfm3_sft160.py','run_lfm3_sft160_pair.py','merge_lfm3_sft160_checkpoint.py','package_lfm3_sft160.py'],
        'evaluation':['evaluate_lfm3_vllm_batched.py','evaluate_lfm3_turblimp.py','score_lfm3_cetvel.py','score_cetvel_generation.py'],
        'datasets':['prepare_turkish_sft160_dev.py','prepare_turkish_pilot80_sft.py'],
    }
    for folder,names in needed.items():
        files.update(ROOT/'scripts'/folder/name for name in names)
    files.add(ROOT/'scripts/training/setup_lfm3_sft160.sh')
    files.add(ROOT/'AGENTS.md')
    for name in ['finetuning-playbook.md','dataset-guide.md','experiment-guide.md','evaluation-guide.md','reproducibility.md','environment-setup-gotchas.md']:
        files.add(ROOT/'docs'/name)
    for folder in ['exp-007-sft160-lr1e4','exp-008-sft160-lr2e4','sft160-dev-v01','sft-pilot160-v01']:
        files.update(p for p in (BASE/folder).iterdir() if p.is_file())
    for name in ['config-planned.json','turblimp-manifest-v01.json','requirements-gpu.txt','data-local/questions-500.jsonl','data-local/turblimp-1600.jsonl']:
        files.add(BASE/'exp-000-baseline'/name)
    files.update(BASE/name for name in ['PILOT160-PAIR-PLAN.md','SFT160-POD-HANDOFF.md'])
    DEST.mkdir(exist_ok=True)
    archive=DEST/'sft160-pod-source.tar.gz'
    hashes={}
    with tarfile.open(archive,'w:gz') as tar:
        for path in sorted(files):
            assert path.is_file(),path
            assert '.env' not in path.name and path.stat().st_size<5_000_000,path
            # Normalize only newlines, never semantic Unicode content.
            data=path.read_bytes().replace(b'\r\n',b'\n')
            assert not re.search(rb'(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{25,}|sk-[A-Za-z0-9_-]{25,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)',data),path
            name=path.relative_to(ROOT).as_posix()
            info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o755 if name.endswith('.sh') else 0o644;info.mtime=0
            tar.addfile(info,io.BytesIO(data));hashes[name]=hashlib.sha256(data).hexdigest()
    # Verify every archived byte against the planned manifest, not just member count.
    with tarfile.open(archive,'r:gz') as tar:
        assert set(tar.getnames())==set(hashes)
        for member in tar:
            assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==hashes[member.name]
    manifest=dict(archive=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size,
        files=hashes,credentials_included=False,private_key_included=False,model_weights_included=False,
        note='Exact frozen benchmark packets are transfer-only, not training. Archive is ignored locally, not published.')
    (DEST/'sft160-pod-source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='files'}))


if __name__=='__main__':main()
