"""Parallel read-only artifact retrieval with complete SHA verification."""
import argparse
import concurrent.futures
import hashlib
from pathlib import Path
import re
import subprocess
import time
from pod_lfm3_session import SSH

def main():
    p=argparse.ArgumentParser();p.add_argument('remote');p.add_argument('local',type=Path);a=p.parse_args()
    assert re.fullmatch(r'/workspace/[A-Za-z0-9_./-]+',a.remote)
    meta=subprocess.check_output(SSH+[f'stat -c%s {a.remote}; sha256sum {a.remote}'],timeout=60).decode().splitlines()
    size=int(meta[0]);digest=meta[1].split()[0]
    dest=a.local;dest.parent.mkdir(parents=True,exist_ok=True)
    parts=dest.with_suffix(dest.suffix+'.chunks');parts.mkdir(exist_ok=True)
    chunk=1024*1024
    def fetch(i):
        count=min(chunk,size-i*chunk);out=parts/f'{i:05d}'
        if out.exists() and out.stat().st_size==count:return
        for attempt in range(5):
            try:
                result=subprocess.run(SSH+[f'dd if={a.remote} bs={chunk} skip={i} count=1 status=none'],capture_output=True,timeout=150)
                assert result.returncode==0 and len(result.stdout)==count,(i,len(result.stdout),count)
                out.write_bytes(result.stdout)
                if i%50==0:print('downloaded',i,flush=True)
                return
            except Exception:
                if attempt==4:raise
                time.sleep(2)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:list(pool.map(fetch,range((size+chunk-1)//chunk)))
    h=hashlib.sha256()
    with dest.with_suffix(dest.suffix+'.partial').open('wb') as f:
        for i in range((size+chunk-1)//chunk):
            b=(parts/f'{i:05d}').read_bytes();h.update(b);f.write(b)
    assert h.hexdigest()==digest
    dest.with_suffix(dest.suffix+'.partial').replace(dest)
    print('DOWNLOAD_VERIFIED',digest,size,flush=True)

if __name__=='__main__':main()
