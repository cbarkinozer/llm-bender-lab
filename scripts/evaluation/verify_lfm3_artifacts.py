"""Verify downloaded bundle/receipt without extracting source text or adapters."""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import tarfile


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    args=parser.parse_args()
    receipt=json.loads(args.receipt.read_text())
    if hashlib.sha256(args.archive.read_bytes()).hexdigest()!=receipt['archive_sha256']:
        raise ValueError('Archive checksum mismatch')
    with tarfile.open(args.archive,'r:gz') as archive:
        members=archive.getmembers()
        if len(members)!=len(receipt['files']) or {m.name for m in members}!=set(receipt['files']):
            raise ValueError('Unexpected, missing or duplicate archive members')
        for member in members:
            path=PurePosixPath(member.name)
            if not member.isfile() or path.is_absolute() or '..' in path.parts:
                raise ValueError('Unsafe archive member')
            if hashlib.sha256(archive.extractfile(member).read()).hexdigest()!=receipt['files'][member.name]:
                raise ValueError('Member checksum mismatch')
    print(json.dumps(dict(status='verified',file_count=len(members),
        note='Integrity verified; experiment completion requires separate output-count and result checks')))


if __name__=='__main__':
    main()
