"""Urgent pod-deletion gate: final adapters and all essential evidence recovered."""
import argparse
import json
from pathlib import Path
import tarfile
from archive_pair import sha
from import_comparison import load

def read(path): return json.loads(path.read_text(encoding='utf-8'))

def main():
    p=argparse.ArgumentParser(); p.add_argument('--artifact-root',type=Path,required=True); a=p.parse_args()
    root=a.artifact_root.resolve(); meta=read(root/'exp015-exp016-essential-backup.json')
    archive=root/meta['archive']
    assert archive.resolve().is_relative_to(root)
    assert archive.stat().st_size==meta['bytes'] and sha(archive)==meta['sha256']
    extracted=root/'essential-extracted'
    if not extracted.exists():
        with tarfile.open(archive,'r:gz') as stream:
            for member in stream.getmembers():
                assert (extracted/member.name).resolve().is_relative_to(extracted.resolve())
                assert not member.name.startswith('/') and (member.isfile() or member.isdir())
            extracted.mkdir(); stream.extractall(extracted,filter='data')
    inventory=read(extracted/'exp015-exp016-essential-file-manifest.json')
    assert len(inventory['files'])==meta['files']
    for name,expected in inventory['files'].items():
        file=extracted/name
        assert file.resolve().is_relative_to(extracted.resolve())
        assert file.stat().st_size==expected['bytes'] and sha(file)==expected['sha256'],name
    runs=extracted/'exp015-exp016-runs'; arms=load(runs)
    for arm,count in [('E',80),('F',104)]:
        sft=runs/arm/'sft-v1'
        assert read(sft/'result.json')['status']=='completed'
        assert read(sft/'source-config.json')['dataset']['train_rows']==count
        args=read(sft/'effective-training-arguments.json')
        assert args['max_steps']==40 and args['learning_rate']==1e-4 and args['gradient_accumulation_steps']==8
        assert read(sft/'checkpoints/checkpoint-40/trainer_state.json')['global_step']==40
        assert read(runs/arm/'wandb-summary.json')['state']=='finished'
        manifest,_=arms[arm]
        assert manifest['adapter_hashes']=={file.name:sha(file) for file in (sft/'adapter').iterdir() if file.is_file()}
        assert manifest['native_eos_count']==32
    report=dict(status='essential-recovery-verified-pod-can-be-deleted',files_sha256_verified=meta['files'],
        archive_sha256=meta['sha256'],bytes=meta['bytes'],final_adapters=['E','F'],outputs_verified=128,
        prompt_parity=True,exact_checkpoint_resume_available=False,omitted=inventory['omitted'],extracted=str(extracted))
    (root/'essential-recovery-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__': main()
