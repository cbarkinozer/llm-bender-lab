"""Immutable complete-run recovery bundle, including diagnostic failures/evidence."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT=Path('/workspace')
RUNS=ROOT/'exp015-exp016-runs'

def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            value.update(block)
    return value.hexdigest()

def main():
    assert json.loads((RUNS/'status.json').read_text())['status']=='completed'
    for arm in ('E','F'):
        folder=RUNS/arm
        for step in (30,40):
            checkpoint=folder/f'sft-v1/checkpoints/checkpoint-{step}'
            for name in ('adapter_model.safetensors','optimizer.pt','scheduler.pt','rng_state.pth','trainer_state.json','training_args.bin'):
                assert (checkpoint/name).is_file(),checkpoint/name
        assert (folder/'sft-v1/adapter/adapter_model.safetensors').is_file()
        exposures=[json.loads(s) for s in (folder/'sft-v1/training-exposure.jsonl').read_text().splitlines()]
        assert len(exposures)==320 and max(r['optimizer_step_before'] for r in exposures)==39
        (folder/'exposure-summary.json').write_text(json.dumps(dict(microbatches=len(exposures),
            supervised_tokens=sum(r['supervised_tokens'] for r in exposures),input_tokens=sum(r['input_tokens'] for r in exposures)),indent=2)+'\n')
    for arm in ('base','C','E','F'):
        manifest=json.loads((RUNS/(arm+'-evaluation-v1')/'manifest.json').read_text())
        assert manifest['status']=='completed' and manifest['count']==32
    (RUNS/'hardware.txt').write_text(subprocess.check_output(['nvidia-smi','-q'],text=True))
    (RUNS/'runtime-python.txt').write_text(subprocess.check_output([sys.executable,'-VV'],text=True))
    members=[RUNS,ROOT/'.cache/wandb',ROOT/'wheels',ROOT/'comparators/C-adapter',ROOT/'exp015-exp016-setup.log',
        ROOT/'exp010-training-freeze.txt',ROOT/'exp015-exp016-source.bundle',ROOT/'setup-exp015-exp016.sh',ROOT/'requirements-exp009.txt',
        ROOT/'archive_pair.py']
    if (ROOT/'exp015-exp016-source-resume.bundle').exists():
        members.append(ROOT/'exp015-exp016-source-resume.bundle')
    if (ROOT/'transfer_backup.py').exists():
        members.append(ROOT/'transfer_backup.py')
    inventory={str(file.relative_to(ROOT)):dict(sha256=sha(file),bytes=file.stat().st_size)
        for member in members for file in (sorted(member.rglob('*')) if member.is_dir() else [member]) if file.is_file()}
    assert not any(Path(name).name=='.env' or Path(name).suffix in ('.pem','.key') for name in inventory)
    (RUNS/'backup-file-manifest.json').write_text(json.dumps(inventory,indent=2)+'\n')
    archive=ROOT/'exp015-exp016-backup.tar.gz'
    assert not archive.exists(),'Refusing overwrite'
    with tarfile.open(archive,'w:gz',dereference=True) as out:
        for member in members:
            out.add(member,arcname=str(member.relative_to(ROOT)))
    result=dict(archive=archive.name,sha256=sha(archive),bytes=archive.stat().st_size,files=len(inventory),
        base_weights='Pinned public weights are a download dependency, excluded from archive',
        source_commit=json.loads((RUNS/'E/sft-v1/environment.json').read_text())['git_commit'],
        training_source_commits={arm:json.loads((RUNS/arm/'sft-v1/environment.json').read_text())['git_commit'] for arm in ('E','F')})
    (ROOT/'exp015-exp016-backup.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':
    main()
