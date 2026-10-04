"""User-requested urgent final-adapter recovery; explicitly excludes resume weights."""
import json
from pathlib import Path
import tarfile
from archive_pair import sha

ROOT=Path('/workspace')
RUNS=ROOT/'exp015-exp016-runs'

def main():
    assert json.loads((RUNS/'status.json').read_text())['status']=='completed'
    full=json.loads((RUNS/'backup-file-manifest.json').read_text())
    selected={}
    for name,expected in full.items():
        path=ROOT/name
        final=any(name.startswith(f'exp015-exp016-runs/{arm}/sft-v1/adapter/') for arm in ('E','F'))
        small=path.suffix in ('.json','.jsonl','.log','.txt','.jinja','.py','.sh','.bundle','.wandb','.md')
        if (final or small) and 'comparators/C-adapter/' not in name:
            assert sha(path)==expected['sha256'],name
            selected[name]=expected
    for arm in ('E','F'):
        assert f'exp015-exp016-runs/{arm}/sft-v1/adapter/adapter_model.safetensors' in selected
    info=dict(scope='urgent-essential-final-adapters-and-complete-text-evidence',files=selected,
        omitted='Optimizer/scheduler/RNG resume binaries; intermediate checkpoint weights; diagnostic adapter weights; CUDA wheel and comparator C weights already present in prior verified local recovery. Completed SFT can be repeated from pinned source/data/config, but these essentials do not support exact checkpoint resume.',
        full_archive_sha256=json.loads((ROOT/'exp015-exp016-backup.json').read_text())['sha256'])
    index=ROOT/'exp015-exp016-essential-file-manifest.json'
    index.write_text(json.dumps(info,indent=2)+'\n')
    archive=ROOT/'exp015-exp016-essentials.tar.gz'
    assert not archive.exists()
    with tarfile.open(archive,'w:gz',dereference=True) as out:
        for name in sorted(selected):
            out.add(ROOT/name,arcname=name,recursive=False)
        out.add(index,arcname=index.name)
        out.add(Path(__file__),arcname='archive_essentials.py')
    meta=dict(archive=archive.name,sha256=sha(archive),bytes=archive.stat().st_size,files=len(selected),scope=info['scope'])
    (ROOT/'exp015-exp016-essential-backup.json').write_text(json.dumps(meta,indent=2)+'\n')
    parts=[]
    with archive.open('rb') as stream:
        index=0
        while block:=stream.read(4*1024*1024):
            file=ROOT/f'exp015-exp016-essential.part-{index:03d}'
            assert not file.exists()
            file.write_bytes(block)
            parts.append(dict(name=file.name,bytes=len(block),sha256=sha(file))); index+=1
    (ROOT/'exp015-exp016-essential-transfer.json').write_text(json.dumps(dict(archive=meta,parts=parts),indent=2)+'\n')
    print(json.dumps(dict(**meta,parts=len(parts))),flush=True)

if __name__=='__main__': main()
