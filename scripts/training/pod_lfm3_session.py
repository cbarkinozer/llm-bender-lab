"""Local SSH transport; byte stdin preserves LF on Windows. No credentials logged."""
import argparse
import subprocess
from pathlib import Path

SSH = ['ssh','-i',str(Path.home()/'.ssh/id_ed25519_lfm3_bilingual'),'-p','38402',
       '-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','ConnectTimeout=25',
       '-o','StrictHostKeyChecking=accept-new','root@ssh5.vast.ai']

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('script',type=Path);a=p.parse_args()
    result=subprocess.run(SSH+['bash -s'],input=a.script.read_bytes().replace(b'\r\n',b'\n'))
    raise SystemExit(result.returncode)
