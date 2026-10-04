"""Verify immutable E/F archive and every indexed file after bounded extraction."""
import argparse
import json
from pathlib import Path
import tarfile
from archive_pair import sha

def main():
    p=argparse.ArgumentParser(); p.add_argument('--artifact-root',type=Path,required=True); a=p.parse_args()
    root=a.artifact_root.resolve()
    meta=json.loads((root/'exp015-exp016-backup.json').read_text())
    archive=root/meta['archive']
    assert archive.resolve().is_relative_to(root)
    assert archive.stat().st_size==meta['bytes'] and sha(archive)==meta['sha256']
    extracted=root/'backup-extracted'
    if not extracted.exists():
        with tarfile.open(archive,'r:gz') as stream:
            for member in stream.getmembers():
                assert (extracted/member.name).resolve().is_relative_to(extracted.resolve())
                assert not member.name.startswith('/') and (member.isfile() or member.isdir())
            extracted.mkdir()
            stream.extractall(extracted,filter='data')
    inventory=json.loads((extracted/'exp015-exp016-runs/backup-file-manifest.json').read_text())
    assert len(inventory)==meta['files']
    for name,expected in inventory.items():
        file=extracted/name
        assert file.resolve().is_relative_to(extracted.resolve())
        assert file.stat().st_size==expected['bytes'] and sha(file)==expected['sha256'],name
    print(json.dumps(dict(archive_sha256_verified=True,files_sha256_verified=len(inventory),extracted=str(extracted))))

if __name__=='__main__':
    main()
