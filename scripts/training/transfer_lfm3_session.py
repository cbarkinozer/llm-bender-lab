"""Checksummed parallel SSH upload; interrupted complete chunks are reusable."""
import argparse
import concurrent.futures
import hashlib
from pathlib import Path
import subprocess
import time
from pod_lfm3_session import SSH

def main():
    p=argparse.ArgumentParser();p.add_argument('archive',type=Path);a=p.parse_args()
    data=a.archive.read_bytes();digest=hashlib.sha256(data).hexdigest()
    root='/workspace/uploads/'+digest
    subprocess.run(SSH+['mkdir -p '+root],check=True)
    size=1024*1024
    def upload(i):
        chunk=data[i*size:(i+1)*size];dest=root+f'/chunk-{i:05d}'
        for attempt in range(5):
            try:
                command=f'if test -f {dest} && test $(stat -c%s {dest}) = {len(chunk)}; then cat > /dev/null; else cat > {dest}.part && mv {dest}.part {dest}; fi'
                r=subprocess.run(SSH+[command],input=chunk,capture_output=True,timeout=150)
                assert r.returncode==0,r.stderr.decode(errors='replace')
                if i%25==0:print('uploaded',i,flush=True)
                return
            except Exception:
                if attempt==4:raise
                time.sleep(2)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:list(pool.map(upload,range((len(data)+size-1)//size)))
    command=f"cat {root}/chunk-* > {root}/input.tar.gz && echo '{digest}  {root}/input.tar.gz' | sha256sum -c - && tar xzf {root}/input.tar.gz -C /workspace/repos/llm-bender-lab"
    subprocess.run(SSH+[command],check=True)
    print('TRANSFER_VERIFIED',digest,len(data),flush=True)

if __name__=='__main__':main()
