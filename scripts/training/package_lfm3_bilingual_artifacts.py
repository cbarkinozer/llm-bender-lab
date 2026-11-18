"""Package adapters and small reproducibility artifacts; never full model weights."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
import time

from run_lfm3_bilingual_gpu import BASE,ROOT,RUN,EXPERIMENTS,read,dump,sha


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--kind',choices=['training','all'],required=True)
    args=parser.parse_args()
    assert (RUN/'training-completion.json').exists()
    if args.kind=='all':
        assert (RUN/'development-completion.json').exists()
    files={}
    for exp in EXPERIMENTS:
        source=BASE/exp
        cfg=read(source/'config.yaml')
        files[source/'config.yaml']=(source/'config.yaml').relative_to(ROOT).as_posix()
        for step in cfg['training']['save_steps']:
            for name in ['adapter_model.safetensors','adapter_config.json','trainer_state.json','training_args.bin']:
                if args.kind=='all' and name=='adapter_model.safetensors':
                    continue  # The training archive already recovered all four identical LoRAs.
                p=source/'results-local/sft'/f'checkpoint-{step}'/name
                if p.exists():files[p]=p.relative_to(ROOT).as_posix()
        for p in (source/'results-local').rglob('*'):
            if not p.is_file() or any(x.startswith('merged-step') for x in p.parts):continue
            if p.suffix in ['.json','.jsonl','.log','.txt','.yaml','.jinja']:
                files[p]=p.relative_to(ROOT).as_posix()
    for p in RUN.rglob('*'):
        if not p.is_file() or any(x in p.parts for x in ['recovery','cpt-merged']):continue
        if args.kind=='training' and 'inference' in p.parts:continue
        if p.suffix in ['.json','.jsonl','.log','.txt','.yaml','.jinja']:
            files[p]=p.relative_to(ROOT).as_posix()
    for p in Path('/workspace/setup-logs').iterdir():
        if p.is_file() and p.suffix in ['.log','.txt']:
            files[p]='pod-operation-logs/'+p.name
    for p in [ROOT/'scripts/training'/name for name in ['run_lfm3_bilingual_gpu.py','run_lfm3_bilingual_pair.py','merge_lfm3_bilingual_checkpoint.py','package_lfm3_bilingual_artifacts.py']]:
        files[p]=p.relative_to(ROOT).as_posix()
    dest=RUN/'recovery';dest.mkdir(parents=True,exist_ok=True)
    archive=dest/(args.kind+'-artifacts.tar.gz')
    entries={}
    with tarfile.open(archive,'w:gz') as tar:
        for path,arc in sorted(files.items(),key=lambda x:x[1]):
            assert 'private-credentials' not in arc and not path.name.endswith('.env')
            data=path.read_bytes() # one consistent snapshot even while logs append
            info=tarfile.TarInfo(arc);info.size=len(data);info.mtime=int(path.stat().st_mtime)
            tar.addfile(info,io.BytesIO(data))
            entries[arc]=dict(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
    assert sum(p.endswith('adapter_model.safetensors') for p in entries)==(4 if args.kind=='training' else 0)
    manifest=dict(kind=args.kind,created_unix=time.time(),archive_sha256=sha(archive),files=entries,
        full_model_weights_included=False,optimizer_states_included=False,
        inference_complete=(RUN/'development-completion.json').exists(),
        adapter_archive_reference='training-artifacts.tar.gz' if args.kind=='all' else None)
    dump(dest/(args.kind+'-manifest.json'),manifest)
    print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,sha256=manifest['archive_sha256'],files=len(entries))),flush=True)


if __name__=='__main__':main()
