"""Resumable verified archive parts; no credential files or shell string evaluation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import time
from archive_pair import sha

def split(root):
    meta=json.loads((root/'exp015-exp016-backup.json').read_text())
    archive=root/meta['archive']
    assert archive.is_file() and sha(archive)==meta['sha256']
    parts=[]
    with archive.open('rb') as stream:
        index=0
        while block:=stream.read(64*1024*1024):
            file=root/f'exp015-exp016-backup.part-{index:03d}'
            assert not file.exists(),'Refusing existing parts'
            file.write_bytes(block)
            parts.append(dict(name=file.name,bytes=len(block),sha256=sha(file)))
            index+=1
    assert sum(p['bytes'] for p in parts)==meta['bytes']
    info=dict(archive=meta,parts=parts)
    (root/'exp015-exp016-transfer.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(dict(parts=len(parts),bytes=meta['bytes'])),flush=True)

def download(a):
    root=a.root.resolve(); root.mkdir(parents=True,exist_ok=True)
    options=['-O','-i',str(a.ssh_key),'-o','BatchMode=yes','-o','ConnectTimeout=15',
        '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','-P',str(a.port)]
    for name in ('exp015-exp016-transfer.json','exp015-exp016-backup.json'):
        subprocess.run(['scp',*options,f'root@{a.host}:/workspace/{name}',str(root/name)],check=True,timeout=120)
    info=json.loads((root/'exp015-exp016-transfer.json').read_text())
    assert info['archive']==json.loads((root/'exp015-exp016-backup.json').read_text())
    def fetch(part):
        assert Path(part['name']).name==part['name']
        path=root/part['name']
        if path.is_file() and path.stat().st_size==part['bytes'] and sha(path)==part['sha256']:
            print('Already verified',part['name'],flush=True); return
        for attempt in range(1,5):
            print('Downloading',part['name'],'attempt',attempt,flush=True)
            try:
                subprocess.run(['scp',*options,f"root@{a.host}:/workspace/{part['name']}",str(path)],check=True,timeout=600)
                assert path.stat().st_size==part['bytes'] and sha(path)==part['sha256'],'Part integrity mismatch'
                print('Verified',part['name'],flush=True); return
            except (subprocess.SubprocessError,AssertionError):
                if attempt==4: raise
                time.sleep(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(fetch,info['parts']))
    archive=root/info['archive']['archive']
    assert archive.resolve().is_relative_to(root)
    if archive.exists():
        assert sha(archive)==info['archive']['sha256'],'Existing archive invalid; never overwrite silently'
    else:
        with archive.open('xb') as out:
            for part in info['parts']:
                with (root/part['name']).open('rb') as stream:
                    shutil.copyfileobj(stream,out,length=1024*1024)
    assert archive.stat().st_size==info['archive']['bytes'] and sha(archive)==info['archive']['sha256']
    print(json.dumps(dict(status='archive-transfer-verified',parts=len(info['parts']),bytes=archive.stat().st_size)),flush=True)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--mode',choices=['split','download'],required=True)
    p.add_argument('--root',type=Path,required=True); p.add_argument('--host'); p.add_argument('--port',type=int)
    p.add_argument('--ssh-key',type=Path); a=p.parse_args()
    if a.mode=='split': split(a.root)
    else:
        assert a.host and a.port and a.ssh_key.is_file()
        download(a)

if __name__=='__main__':
    main()
