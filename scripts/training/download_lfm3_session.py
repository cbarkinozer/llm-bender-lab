"""Pinned minimal model downloads; only root CPT adapter, no historical checkpoints."""
import concurrent.futures
import hashlib
import os
from pathlib import Path
import time

os.environ['HF_HOME']='/workspace/.cache/huggingface'
os.environ['HF_HUB_DISABLE_XET']='1'
import httpx
from huggingface_hub import hf_hub_url,get_hf_file_metadata,snapshot_download

BASE_REV='0dc4268b561499c648c7ba7c9466bf3d8d01517a'
CPT_REV='6f213ec25a944dab2fbdeb6d337deb0e0442e638'

def download(repo,rev,filename):
    for attempt in range(12):
        try:
            meta=get_hf_file_metadata(hf_hub_url(repo,filename,revision=rev));break
        except Exception:
            if attempt==11:raise
            time.sleep(3)
    assert meta.commit_hash==rev and len(meta.etag)==64
    cache=Path(os.environ['HF_HOME'])/'hub'/('models--'+repo.replace('/','--'))
    blob=cache/'blobs'/meta.etag
    blob.parent.mkdir(parents=True,exist_ok=True)
    chunks=Path('/workspace/download-chunks')/repo.replace('/','--');chunks.mkdir(parents=True,exist_ok=True)
    client=httpx.Client(follow_redirects=True,timeout=120,limits=httpx.Limits(max_connections=8,max_keepalive_connections=8))
    size=8*1024*1024
    def fetch(i):
        start=i*size;end=min(meta.size,start+size)-1;p=chunks/f'{i:05d}'
        if p.exists() and p.stat().st_size==end-start+1:return
        for attempt in range(12):
            try:
                with client.stream('GET',meta.location,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'}) as r:
                    assert r.status_code==206 and r.headers.get('content-range','').startswith(f'bytes {start}-{end}/')
                    with p.with_suffix('.part').open('wb') as f:
                        for b in r.iter_bytes():f.write(b)
                assert p.with_suffix('.part').stat().st_size==end-start+1
                p.with_suffix('.part').replace(p);return
            except Exception as e:
                print('retry',repo,i,attempt,type(e).__name__,flush=True);time.sleep(min(15,attempt+1))
        raise RuntimeError(i)
    if not blob.exists():
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(fetch,range((meta.size+size-1)//size)))
        h=hashlib.sha256()
        with blob.with_suffix('.partial').open('wb') as f:
            for p in sorted(chunks.glob('[0-9][0-9][0-9][0-9][0-9]')):
                b=p.read_bytes();h.update(b);f.write(b)
        assert h.hexdigest()==meta.etag
        blob.with_suffix('.partial').replace(blob)
    assert hashlib.sha256(blob.read_bytes()).hexdigest()==meta.etag
    snap=cache/'snapshots'/rev/filename;snap.parent.mkdir(parents=True,exist_ok=True)
    if not snap.exists():snap.symlink_to(blob)
    snapshot_download(repo,revision=rev,allow_patterns=['*.json','*.jinja','*.py','*.txt'],ignore_patterns=['*/*'])
    print('VERIFIED',repo,filename,meta.etag,flush=True)

if __name__=='__main__':
    download('LiquidAI/LFM3-1.7B',BASE_REV,'model.safetensors')
    download('cbarkinozer/LFM3-1.7B-Turkish-CPT',CPT_REV,'adapter_model.safetensors')
    print('DOWNLOADS_DONE',flush=True)
