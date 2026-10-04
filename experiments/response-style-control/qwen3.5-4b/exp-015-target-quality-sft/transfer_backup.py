"""Resumable verified archive parts; no credential files or shell string evaluation."""
import argparse
import hashlib
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import time
from archive_pair import sha

def split(root,chunk_mib,manifest_name):
    meta=json.loads((root/'exp015-exp016-backup.json').read_text())
    archive=root/meta['archive']
    assert archive.is_file() and sha(archive)==meta['sha256']
    parts=[]
    with archive.open('rb') as stream:
        index=0
        while block:=stream.read(chunk_mib*1024*1024):
            prefix='exp015-exp016-backup' if chunk_mib==64 else f'exp015-exp016-backup{chunk_mib}'
            file=root/f'{prefix}.part-{index:03d}'
            assert not file.exists(),'Refusing existing parts'
            file.write_bytes(block)
            parts.append(dict(name=file.name,bytes=len(block),sha256=sha(file)))
            index+=1
    assert sum(p['bytes'] for p in parts)==meta['bytes']
    info=dict(archive=meta,parts=parts)
    (root/manifest_name).write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(dict(parts=len(parts),bytes=meta['bytes'])),flush=True)

def download(a):
    root=a.root.resolve(); root.mkdir(parents=True,exist_ok=True)
    options=['-O','-i',str(a.ssh_key),'-o','BatchMode=yes','-o','ConnectTimeout=15',
        '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','-P',str(a.port)]
    for name in (a.manifest,a.metadata):
        subprocess.run(['scp',*options,f'root@{a.host}:/workspace/{name}',str(root/name)],check=True,timeout=120,capture_output=True,text=True)
    info=json.loads((root/a.manifest).read_text())
    assert info['archive']==json.loads((root/a.metadata).read_text())
    # Smaller chunks can safely reuse even incomplete old64MiB parts. Trust only
    # the new independently recorded hash, not length or a partial-copy success.
    offset=0
    recovered=0
    for part in info['parts']:
        path=root/part['name']
        if not path.exists() and '.part-' in part['name'] and 'backup4.part-' in part['name']:
            old=root/f'exp015-exp016-backup.part-{offset//(64*1024*1024):03d}'
            within=offset%(64*1024*1024)
            if old.exists() and old.stat().st_size>=within+part['bytes']:
                with old.open('rb') as stream:
                    stream.seek(within); block=stream.read(part['bytes'])
                if hashlib.sha256(block).hexdigest()==part['sha256']:
                    path.write_bytes(block)
                    recovered+=1
        offset+=part['bytes']
    print('Recovered hash-verified smaller chunks from previous partial/full parts:',recovered,flush=True)
    def fetch(part):
        assert Path(part['name']).name==part['name']
        path=root/part['name']
        if path.is_file() and path.stat().st_size==part['bytes'] and sha(path)==part['sha256']:
            return
        for attempt in range(1,5):
            print('Downloading',part['name'],'attempt',attempt,flush=True)
            try:
                subprocess.run(['scp',*options,f"root@{a.host}:/workspace/{part['name']}",str(path)],check=True,timeout=600,capture_output=True,text=True)
                assert path.stat().st_size==part['bytes'] and sha(path)==part['sha256'],'Part integrity mismatch'
                print('Verified',part['name'],flush=True); return
            except (subprocess.SubprocessError,AssertionError) as error:
                print('Transfer failed:',part['name'],getattr(error,'stderr',None) or type(error).__name__,flush=True)
                if attempt==4: raise
                time.sleep(2)
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
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
    p.add_argument('--ssh-key',type=Path)
    p.add_argument('--chunk-mib',type=int,default=64)
    p.add_argument('--manifest',default='exp015-exp016-transfer.json')
    p.add_argument('--metadata',default='exp015-exp016-backup.json')
    p.add_argument('--workers',type=int,default=2)
    a=p.parse_args()
    assert a.chunk_mib in (4,8,64) and Path(a.manifest).name==a.manifest and Path(a.metadata).name==a.metadata
    assert 1<=a.workers<=4
    if a.mode=='split': split(a.root,a.chunk_mib,a.manifest)
    else:
        assert a.host and a.port and a.ssh_key.is_file()
        download(a)

if __name__=='__main__':
    main()
