"""Endpoint-parameterized transport for the NEXT pod; never defaults to a dead pod."""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import subprocess
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/turkish-capability/lfm3-1.7b'
DATA=BASE/'stage-diagnostic-v01'
RUN=BASE/'stage-diagnostic-v01-local'

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['upload','start','status','download'])
    p.add_argument('--host',required=True);p.add_argument('--port',required=True,type=int)
    p.add_argument('--key',type=Path,default=Path.home()/'.ssh/id_ed25519_lfm3_bilingual');a=p.parse_args()
    assert a.host and not a.host.startswith('-') and all(c.isalnum() or c in '.-' for c in a.host)
    assert 1<=a.port<=65535 and a.key.is_file()
    ssh=['ssh','-i',str(a.key),'-p',str(a.port),'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','ConnectTimeout=25',
         '-o','StrictHostKeyChecking=accept-new','root@'+a.host]
    if a.action=='upload':
        import transfer_lfm3_session as transfer
        transfer.SSH=ssh;sys.argv=[sys.argv[0],str(RUN/'pod-input.tar.gz')];transfer.main()
    elif a.action=='start':
        # Idempotent completion check, and never start a second live controller.
        script='''set -euo pipefail
cd /workspace/repos/llm-bender-lab
if pgrep -f '^bash scripts/evaluation/run_lfm3_stage_diagnostic.sh$' >/dev/null; then echo ALREADY_RUNNING; exit 0; fi
if test -f experiments/turkish-capability/lfm3-1.7b/stage-diagnostic-v01-local/completion.json; then echo COMPLETED_INSPECT_AND_DOWNLOAD; exit 0; fi
python3 scripts/evaluation/run_lfm3_stage_diagnostic.py verify
if test -f /workspace/stage-controller.log; then mv /workspace/stage-controller.log "/workspace/stage-controller-attempt-$(date -u +%Y%m%dT%H%M%S).log"; fi
R=experiments/turkish-capability/lfm3-1.7b/stage-diagnostic-v01-local
if test -d "$R/logs"; then cp -a "$R/logs" "$R/attempt-logs-$(date -u +%Y%m%dT%H%M%S)"; fi
nohup bash scripts/evaluation/run_lfm3_stage_diagnostic.sh > /workspace/stage-controller.log 2>&1 < /dev/null &
echo controller_pid=$!
'''
        subprocess.run(ssh+['bash -s'],input=script.encode(),check=True)
    elif a.action=='status':
        subprocess.run(ssh+['tail -n 15 /workspace/stage-controller.log; test ! -f /workspace/stage-diagnostic-package.json || cat /workspace/stage-diagnostic-package.json'],check=True)
    else:
        metadata=json.loads(subprocess.check_output(ssh+['cat /workspace/stage-diagnostic-package.json'],timeout=60))
        assert metadata['path']=='/workspace/stage-diagnostic-artifacts.tar.gz' and metadata['contains_full_weights'] is False
        import fetch_lfm3_session as fetch
        archive=RUN/'stage-diagnostic-artifacts.tar.gz';fetch.SSH=ssh
        sys.argv=[sys.argv[0],metadata['path'],str(archive)];fetch.main()
        assert hashlib.sha256(archive.read_bytes()).hexdigest()==metadata['sha256']
        manifest_name=(RUN/'backup-manifest.json').relative_to(ROOT).as_posix();restored={}
        with tarfile.open(archive) as t:
            manifest=json.load(t.extractfile(manifest_name));members=t.getmembers()
            assert len(members)==len(manifest)+1 and {m.name for m in members}==set(manifest)|{manifest_name}
            for m in members:
                pure=PurePosixPath(m.name);dest=ROOT/m.name
                assert m.isfile() and not pure.is_absolute() and '..' not in pure.parts and dest.resolve().is_relative_to(RUN.resolve())
                assert dest.suffix not in ['.safetensors','.pt','.pth']
                data=t.extractfile(m).read();digest=hashlib.sha256(data).hexdigest()
                if m.name!=manifest_name:assert digest==manifest[m.name]
                if dest.exists():assert hashlib.sha256(dest.read_bytes()).hexdigest()==digest,'Preserve differing local artifact'
                else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
                restored[m.name]=digest
        completion=json.loads((RUN/'completion.json').read_text());assert completion['outputs']==264 and not completion['training_performed']
        total=0
        for mode,expected in [('main-off',72),('thinking-on',16)]:
            for model in ['base','cpt','cpt-bilingual69']:
                folder=RUN/'inference'/mode/model
                m=json.loads((folder/'manifest.json').read_text())
                actual=[json.loads(l) for l in (folder/'answers.jsonl').read_text(encoding='utf-8').splitlines()]
                assert m['status']=='completed' and m['count']==len(actual)==expected
                assert len({r['id'] for r in actual})==expected and all(r['raw_output'].strip() for r in actual)
                total+=len(actual)
        assert total==264
        control=subprocess.check_output(ssh+['cat /workspace/stage-controller.log'],timeout=60)
        assert control.decode().rstrip().endswith('ALL_DONE')
        (RUN/'controller.log').write_bytes(control)
        receipt=dict(status='verified',archive=metadata,files_verified=len(manifest),files=restored,
            controller_sha256=hashlib.sha256(control).hexdigest(),no_full_weights_downloaded=True,pod_safe_to_close=True)
        (RUN/'LOCAL-BACKUP-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        print('ALL ARTIFACTS VERIFIED; POD SAFE TO CLOSE')

if __name__=='__main__':main()
