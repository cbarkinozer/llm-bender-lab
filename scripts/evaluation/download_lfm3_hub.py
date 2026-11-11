"""Use the pinned Hub/Xet client for parallel model transfer, then verify hashes."""
import hashlib
import json
from pathlib import Path


def main():
    from huggingface_hub import snapshot_download,HfApi
    repo='LiquidAI/LFM3-1.7B';revision='0dc4268b561499c648c7ba7c9466bf3d8d01517a'
    root=Path(snapshot_download(repo,revision=revision,
        allow_patterns=['*.safetensors','*.json','*.jinja','*.py'],max_workers=4))
    info=HfApi().model_info(repo,revision=revision,files_metadata=True)
    assert info.sha==revision
    rows=[]
    for sibling in info.siblings:
        file=root/sibling.rfilename
        if file.is_file() and file.suffix in ('.safetensors','.json','.jinja','.py'):
            h=hashlib.sha256()
            with file.open('rb') as stream:
                while block:=stream.read(8*1024*1024):
                    h.update(block)
            digest=h.hexdigest()
            expected=sibling.lfs.sha256 if sibling.lfs else None
            assert not expected or expected==digest
            rows.append(dict(name=sibling.rfilename,sha256=digest,bytes=file.stat().st_size,lfs_sha256=expected))
    output=Path('experiments/turkish-capability/lfm3-1.7b/exp-000-baseline/results-local/environment/checkpoint-download.json')
    output.write_text(json.dumps(dict(repo=repo,revision=revision,backend='huggingface-hub/Xet',files=rows),indent=2)+'\n')
    print('Pinned checkpoint hashes verified',flush=True)


if __name__=='__main__':
    main()
