"""Isolated cookbook session transport; never touches other pod projects."""
import argparse, hashlib, io, json, os, subprocess, tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/turkish-capability/lfm3-1.7b'
LOCAL=BASE/'cookbook-runtime-local'
REMOTE='/workspace/lfm3-cookbook/repo'

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['sync','shell','download']);p.add_argument('--command');a=p.parse_args()
    try:host=os.environ['LFM3_POD_HOST'];port=os.environ['LFM3_POD_PORT']
    except KeyError as e:raise SystemExit(f'Set {e.args[0]}; the pod address is not stored in Git')
    ssh=['ssh','-i',str(Path.home()/'.ssh/id_ed25519_lfm3_bilingual'),'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-p',port,f'root@{host}']
    LOCAL.mkdir(parents=True,exist_ok=True)
    if a.action=='shell':
        subprocess.run(ssh+['bash -s'],input=a.command.encode(),check=True)
    elif a.action=='sync':
        files=list((ROOT/'scripts').rglob('*.py'))+list((ROOT/'scripts').rglob('*.sh'))
        for name in ['cookbook-sft-v01','exp-014-completion-mask','exp-015-cookbook-recipe','stage-diagnostic-v01']:
            files.extend(f for f in (BASE/name).rglob('*') if f.is_file() and 'evidence' not in f.parts and 'results-local' not in f.parts and 'references-local-only' not in f.name)
        files += [BASE/'exp-012-base-bilingual/config.yaml',BASE/'exp-000-baseline/config-planned.json',
                  BASE/'bilingual-pilot-v01/revisions/v01-corrections-02/token-budget-and-order.json']
        buffer=io.BytesIO()
        with tarfile.open(fileobj=buffer,mode='w:gz') as t:
            for f in files:
                data=f.read_bytes()
                if f.suffix=='.sh':data=data.replace(b'\r\n',b'\n')
                info=tarfile.TarInfo(f.relative_to(ROOT).as_posix());info.size=len(data);t.addfile(info,io.BytesIO(data))
        subprocess.run(ssh+[f'mkdir -p {REMOTE}; tar xzf - -C {REMOTE}'],input=buffer.getvalue(),check=True)
        print('SYNCED',len(files))
    else:
        meta=json.loads(subprocess.check_output(ssh+['cat /workspace/lfm3-cookbook/backup.json']))
        archive=LOCAL/'artifacts.tar.gz'
        if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest()!=meta['sha256']:
            with archive.open('wb') as f: subprocess.run(ssh+['cat /workspace/lfm3-cookbook/artifacts.tar.gz'],stdout=f,check=True)
        assert hashlib.sha256(archive.read_bytes()).hexdigest()==meta['sha256']
        with tarfile.open(archive) as t:
            for m in t:
                dest=ROOT/m.name
                assert m.isfile() and dest.resolve().is_relative_to(BASE.resolve()) and '..' not in Path(m.name).parts
                data=t.extractfile(m).read();assert hashlib.sha256(data).hexdigest()==meta['files'][m.name]
                if dest.exists():assert dest.read_bytes()==data,'Differing artifact, preserve and inspect'
                else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        (LOCAL/'LOCAL-BACKUP-RECEIPT.json').write_text(json.dumps({**meta,'status':'verified'},indent=2))
        print('VERIFIED',len(meta['files']),'files; no full weights')

if __name__=='__main__':main()
