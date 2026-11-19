"""Restore only a verified manifest-listed artifact archive; never overwrite differing files."""
import hashlib
import json
from pathlib import Path,PurePosixPath
import tarfile

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'experiments/turkish-capability/lfm3-1.7b/preservation-session-v01-local'
EXPECTED='02781191accfb2064f2722cddf8c3cb751ac6a570f4445e8090b5210252c923c'
PREFIX='repos/llm-bender-lab/'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    archive=RUN/'preservation-artifacts.tar.gz';assert sha(archive)==EXPECTED
    manifest_name=PREFIX+'experiments/turkish-capability/lfm3-1.7b/preservation-session-v01-local/backup-manifest.json'
    with tarfile.open(archive) as t:
        manifest=json.load(t.extractfile(manifest_name));assert len(manifest)==189
        members=t.getmembers();assert {m.name for m in members}==set(manifest)|{manifest_name}
        restored={};adapters={}
        for m in members:
            path=PurePosixPath(m.name);assert m.isfile() and not path.is_absolute() and '..' not in path.parts
            if m.name.startswith(PREFIX):dest=ROOT/m.name[len(PREFIX):]
            else:dest=RUN/'remote-workspace'/m.name
            assert dest.resolve().is_relative_to(ROOT.resolve())
            if dest.suffix=='.safetensors':
                assert dest.name=='adapter_model.safetensors' and dest.parent.name in ['checkpoint-69','checkpoint-113']
            data=t.extractfile(m).read();digest=hashlib.sha256(data).hexdigest()
            if m.name!=manifest_name:assert digest==manifest[m.name],m.name
            if dest.exists():assert sha(dest)==digest,('Differing existing artifact: preserve and inspect',str(dest))
            else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
            assert sha(dest)==digest
            restored[str(dest.relative_to(ROOT)).replace('\\','/')]=digest
            if dest.suffix=='.safetensors':adapters[str(dest.relative_to(ROOT)).replace('\\','/')]=digest
    assert len(adapters)==4
    inference=list((RUN/'inference').rglob('answers.jsonl'))
    count=sum(len(p.read_text(encoding='utf-8').splitlines()) for p in inference)
    assert len(inference)==12 and count==240
    receipt=dict(status='verified',archive_sha256=EXPECTED,archive_bytes=archive.stat().st_size,
        manifest_files_verified=189,inference_files=12,inference_outputs=240,adapters=adapters,
        no_base_or_merged_weights_downloaded=True,files=restored)
    (RUN/'LOCAL-BACKUP-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='files'},indent=2))

if __name__=='__main__':main()
