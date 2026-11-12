"""Package only this experiment and its entrypoints; verify every archived file.

Use before transfer and again on the pod after results/adapters are saved under
the experiment folder. Output must be outside the archived experiment tree.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=args.repo_root.resolve()
    experiment=root/'experiments/turkish-capability/lfm3-1.7b'
    output=args.output.resolve()
    if output.is_relative_to(experiment.resolve()):
        raise ValueError('Archive output must be outside experiment tree')
    files=[p for p in experiment.rglob('*') if p.is_file()]
    for folder,pattern in [('datasets','*lfm3*.py'),('evaluation','*lfm3*.py'),('training','*lfm3*.py')]:
        files.extend((root/'scripts'/folder).glob(pattern))
    files += [root/'scripts/datasets/restore_cetvel_comparison.py',root/'scripts/evaluation/score_cetvel_generation.py']
    historical=root/'experiments/turkish-capability/qwen3.5-4b/exp-003-cetvel-500'
    files += [historical/name for name in ('prepare.py','data-v1/manifest.json',
        'data-v1/tokenization-profile.json','results-v1/base/manifest.json','results-v1/comparison.json')]
    files += [root/'AGENTS.md']
    files += [root/'docs'/name for name in ('environment-setup-gotchas.md','finetuning-playbook.md',
        'dataset-guide.md','evaluation-guide.md','reproducibility.md','experiment-guide.md')]
    files=sorted(set(p.absolute() for p in files if '__pycache__' not in p.parts))
    evidence={}
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():
        raise ValueError('Refusing to overwrite archive')
    for path in files:
        if not path.is_relative_to(root):
            raise ValueError('Unsafe archive source')
        if path.is_symlink() and not ('wandb' in path.parts and path.suffix=='.log'):
            raise ValueError('Unexpected artifact symlink')
        if path.name.startswith('.env') or path.suffix.lower() in ('.pem','.key'):
            raise ValueError('Credential-like path in artifact scope')
        evidence[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    with tarfile.open(output,'w:gz',dereference=True) as archive:
        for path in files:
            archive.add(path,arcname=path.relative_to(root).as_posix(),recursive=False)
    with tarfile.open(output,'r:gz') as archive:
        for name,expected in evidence.items():
            actual=hashlib.sha256(archive.extractfile(name).read()).hexdigest()
            if actual!=expected:
                raise ValueError('Archive member verification failed')
    receipt=dict(status='all_members_hash_verified',file_count=len(evidence),
        archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),archive_bytes=output.stat().st_size,files=evidence,
        warning='Contains source-bearing benchmark/training text; private transfer, not a public dataset release')
    output.with_suffix(output.suffix+'.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='files'}))


if __name__=='__main__':
    main()
