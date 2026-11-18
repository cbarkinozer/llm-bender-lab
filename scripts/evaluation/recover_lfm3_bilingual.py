"""Recover and hash-verify a pod archive containing four LoRAs and small artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/turkish-capability/lfm3-1.7b'
RUN=BASE/'bilingual-runtime-local'
KEY=Path.home()/'.ssh/id_ed25519_lfm3_bilingual'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--kind',choices=['training','all'],required=True)
    parser.add_argument('--local-archive',action='store_true',help='Verify/extract an already downloaded and reconstructed archive')
    args=parser.parse_args()
    dest=BASE/'preparation-local/bilingual-pod/recovery';dest.mkdir(parents=True,exist_ok=True)
    remote='/workspace/repos/llm-bender-lab/experiments/turkish-capability/lfm3-1.7b/bilingual-runtime-local/recovery/'
    names=[args.kind+'-manifest.json',args.kind+'-artifacts.tar.gz']
    if not args.local_archive:
        for name in names:
            subprocess.run(['scp','-i',str(KEY),'-P','33292','root@ssh7.vast.ai:'+remote+name,str(dest/name)],check=True)
    manifest=json.loads((dest/names[0]).read_text(encoding='utf-8'))
    archive=dest/names[1]
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['archive_sha256']
    allowed=['experiments/turkish-capability/lfm3-1.7b/bilingual-runtime-local/',
             'experiments/turkish-capability/lfm3-1.7b/exp-010-tr-only-sft160/',
             'experiments/turkish-capability/lfm3-1.7b/exp-011-bilingual-sft640/',
             'scripts/training/','pod-operation-logs/']
    with tarfile.open(archive,'r:gz') as tar:
        members=tar.getmembers()
        assert len(members)==len(manifest['files'])
        for member in members:
            assert member.isfile() and any(member.name.startswith(p) for p in allowed)
            data=tar.extractfile(member).read()
            assert hashlib.sha256(data).hexdigest()==manifest['files'][member.name]['sha256']
            assert len(data)==manifest['files'][member.name]['bytes']
            # Keep immutable pod copies of live scripts/configs rather than overwrite local work.
            relative=Path(member.name)
            if member.name.startswith('pod-operation-logs/'):
                target=RUN/'operation-logs'/relative.name
            elif member.name.startswith('scripts/') or member.name.endswith('/config.yaml'):
                target=RUN/'pod-source'/relative
            else:
                target=ROOT/relative
            assert ROOT.resolve() in target.resolve().parents
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
    receipt=dict(kind=args.kind,archive_sha256=manifest['archive_sha256'],verified_files=len(manifest['files']),
        adapters=sum(p.endswith('adapter_model.safetensors') for p in manifest['files']),
        adapter_archive_reference=manifest.get('adapter_archive_reference'),
        full_weights_downloaded=False,inference_complete=manifest['inference_complete'])
    path=BASE/('BILINGUAL-'+args.kind.upper()+'-BACKUP.json')
    path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
