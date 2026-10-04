"""Read-only archived per-file integrity check before long transfers."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

def main():
    p=argparse.ArgumentParser(); p.add_argument('--archive',type=Path,required=True); a=p.parse_args()
    with tarfile.open(a.archive,'r:gz') as stream:
        inventory=json.load(stream.extractfile('exp015-exp016-runs/backup-file-manifest.json'))
        verified=set()
        for member in stream:
            if not member.isfile() or member.name not in inventory: continue
            expected=inventory[member.name]
            assert member.size==expected['bytes']
            value=hashlib.sha256()
            with stream.extractfile(member) as file:
                for block in iter(lambda:file.read(1024*1024),b''):
                    value.update(block)
            assert value.hexdigest()==expected['sha256'],member.name
            verified.add(member.name)
        assert verified==set(inventory)
    print(json.dumps(dict(status='archived-file-integrity-verified',files=len(verified))))

if __name__=='__main__':
    main()
