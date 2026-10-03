"""Archive completed paired runs and dereferenced W&B files, with per-file hashes."""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

ROOT=Path('/workspace')
RUNS=ROOT/'exp011-exp012-runs'

def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda:file.read(1024*1024),b''):
            digest.update(block)
    return digest.hexdigest()

def main():
    assert json.loads((RUNS/'status.json').read_text())['status']=='completed'
    for arm in ('A','B'):
        root=RUNS/arm
        for step in (30,40):
            checkpoint=root/f'sft-v1/checkpoints/checkpoint-{step}'
            for name in ('adapter_model.safetensors','optimizer.pt','scheduler.pt','rng_state.pth','trainer_state.json','training_args.bin'):
                assert (checkpoint/name).is_file(),checkpoint/name
        assert (root/'sft-v1/adapter/adapter_model.safetensors').is_file()
        assert json.loads((root/'validation-v1/manifest.json').read_text())['count']==20
    hardware=subprocess.check_output(['nvidia-smi','-q'],text=True)
    (RUNS/'hardware.txt').write_text(hardware)
    members=[RUNS,ROOT/'.cache/wandb',ROOT/'exp011-exp012-setup.log',ROOT/'exp010-training-freeze.txt',
        ROOT/'exp011-exp012-source.bundle',ROOT/'exp011-exp012-source-complete.bundle']
    optional=ROOT/'exp011-exp012-source-diagnostics.bundle'
    if optional.exists():
        members.append(optional)
    inventory={str(file.relative_to(ROOT)):dict(sha256=sha(file),bytes=file.stat().st_size)
        for member in members for file in (sorted(member.rglob('*')) if member.is_dir() else [member]) if file.is_file()}
    # Archive itself is outside all members; all external W&B symlinks are dereferenced.
    index=RUNS/'backup-file-manifest.json'
    index.write_text(json.dumps(inventory,indent=2)+'\n')
    archive=ROOT/'exp011-exp012-backup.tar.gz'
    assert not archive.exists()
    with tarfile.open(archive,'w:gz',dereference=True) as output:
        for member in members:
            output.add(member,arcname=str(member.relative_to(ROOT)))
    result=dict(archive=archive.name,sha256=sha(archive),bytes=archive.stat().st_size,files=len(inventory),
        base_weights='Pinned public weights remain an explicit download dependency, not included.',
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    (ROOT/'exp011-exp012-backup.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':
    main()
