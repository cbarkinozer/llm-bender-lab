"""Verify and safely extract small completed inference evidence ahead of full recovery."""
import argparse
from pathlib import Path
import tarfile
from archive_pair import sha

def main():
    p=argparse.ArgumentParser(); p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--sha256',required=True); p.add_argument('--output-dir',type=Path,required=True); a=p.parse_args()
    assert sha(a.archive)==a.sha256 and not a.output_dir.exists()
    root=a.output_dir.resolve()
    with tarfile.open(a.archive,'r:gz') as stream:
        for member in stream.getmembers():
            assert (root/member.name).resolve().is_relative_to(root)
            assert not member.name.startswith('/') and (member.isfile() or member.isdir())
        root.mkdir()
        stream.extractall(root,filter='data')
    print('Verified and extracted completed inference evidence')

if __name__=='__main__':
    main()
