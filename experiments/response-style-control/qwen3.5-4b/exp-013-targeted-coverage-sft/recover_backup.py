"""Verify archive identity and bounded extraction, then verify every recovered file."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from verify_backup import sha


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--artifact-root',type=Path,required=True)
    args=p.parse_args()
    root=args.artifact_root.resolve()
    meta=json.loads((root/'exp013-exp014-backup.json').read_text(encoding='utf-8'))
    archive=root/meta['archive']
    assert archive.resolve().is_relative_to(root)
    assert archive.stat().st_size==meta['bytes'] and sha(archive)==meta['sha256']
    extracted=root/'backup-extracted'
    if not extracted.exists():
        with tarfile.open(archive,'r:gz') as tar:
            for member in tar.getmembers():
                target=(extracted/member.name).resolve()
                if not target.is_relative_to(extracted.resolve()) or member.name.startswith('/'):
                    raise ValueError('Archive target escapes recovery root: '+member.name)
                if not (member.isfile() or member.isdir()):
                    raise ValueError('Archive links/devices not allowed: '+member.name)
            extracted.mkdir()
            tar.extractall(extracted,filter='data')
    subprocess.run([sys.executable,str(Path(__file__).with_name('verify_backup.py')),
                    '--root',str(extracted)],check=True)
    print(json.dumps(dict(archive_sha256_verified=True,extracted=str(extracted),files=meta['files'])))


if __name__=='__main__':
    main()
