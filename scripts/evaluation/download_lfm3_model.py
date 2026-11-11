"""Download the pinned executable checkpoint; verify LFS hashes when available."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import urllib.request


def main():
    repo='LiquidAI/LFM3-1.7B'
    revision='0dc4268b561499c648c7ba7c9466bf3d8d01517a'
    with urllib.request.urlopen(f'https://huggingface.co/api/models/{repo}/revision/{revision}?blobs=true') as response:
        info=json.load(response)
    assert info['sha']==revision
    root=Path('/workspace/.cache/huggingface/hub/models--LiquidAI--LFM3-1.7B/snapshots')/revision
    root.mkdir(parents=True,exist_ok=True)
    def download(row):
        name=row['rfilename']
        if '/' in name or not name.endswith(('.safetensors','.json','.jinja','.py')):
            return None
        target=root/name
        if not target.exists():
            temporary=target.with_suffix(target.suffix+'.partial')
            with urllib.request.urlopen(f'https://huggingface.co/{repo}/resolve/{revision}/{name}',timeout=120) as source, temporary.open('wb') as output:
                while block:=source.read(8*1024*1024):
                    output.write(block)
            temporary.rename(target)
        digest=hashlib.sha256(target.read_bytes()).hexdigest()
        expected=row.get('lfs',{}).get('sha256')
        if expected and digest!=expected:
            raise ValueError('Checkpoint hash mismatch: '+name)
        print(name+' verified '+digest,flush=True)
        return dict(name=name,sha256=digest,bytes=target.stat().st_size,lfs_sha256=expected)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results=[r for r in pool.map(download,info['siblings']) if r]
    output=Path('experiments/turkish-capability/lfm3-1.7b/exp-000-baseline/results-local/environment/checkpoint-download.json')
    output.write_text(json.dumps(dict(repo=repo,revision=revision,files=results),indent=2)+'\n')


if __name__=='__main__':
    main()
