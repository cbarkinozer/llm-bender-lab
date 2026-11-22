"""Transport for the eval v2 GPU session: sync inputs to the pod, run commands, fetch verified results.

Set LFM3_POD_HOST and LFM3_POD_PORT (never stored in Git). Optional LFM3_POD_KEY overrides the SSH key.
Only small files move: scripts, eval v2 packets, two LoRA adapters; results come back as a checksummed tarball
without model weights.
"""
import argparse
import hashlib
import io
import os
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
EVAL = BASE / 'eval-v2'
REMOTE = '/workspace/lfm3-evalv2'
RESULTS_LOCAL = EVAL / 'runs-local'
ADAPTER_FILES = ('adapter_model.safetensors', 'adapter_config.json')
ADAPTERS = ('exp-014-completion-mask', 'exp-015-cookbook-recipe')


def ssh_command():
    try:
        host, port = os.environ['LFM3_POD_HOST'], os.environ['LFM3_POD_PORT']
    except KeyError as error:
        raise SystemExit(f'Set {error.args[0]}; the pod address is not stored in Git')
    key = os.environ.get('LFM3_POD_KEY', str(Path.home() / '.ssh/id_ed25519_lfm3_bilingual'))
    return ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes', '-p', port, f'root@{host}']


def sync_files():
    files = list((ROOT / 'scripts').rglob('*.py')) + list((ROOT / 'scripts').rglob('*.sh'))
    files = [f for f in files if '__pycache__' not in f.parts]
    files += [f for f in EVAL.rglob('*') if f.is_file() and 'runs-local' not in f.parts and 'source-cache' not in f.parts]
    files.append(BASE / 'exp-000-baseline/config-planned.json')
    for experiment in ADAPTERS:
        for name in ADAPTER_FILES:
            path = BASE / experiment / 'results-local/sft/adapter' / name
            if not path.exists():
                raise SystemExit(f'Missing adapter file: {path}')
            files.append(path)
    return files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['sync', 'shell', 'download'])
    parser.add_argument('--command', help='Shell command for the shell action')
    args = parser.parse_args()
    ssh = ssh_command()
    if args.action == 'shell':
        if not args.command:
            parser.error('--command is required')
        subprocess.run(ssh + ['bash -s'], input=args.command.encode(), check=True)
    elif args.action == 'sync':
        files = sync_files()
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
            for path in files:
                data = path.read_bytes()
                if path.suffix in ('.sh', '.py', '.json', '.md'):
                    data = data.replace(b'\r\n', b'\n')  # Windows CRLF corrupts scripts on Linux
                info = tarfile.TarInfo(path.relative_to(ROOT).as_posix())
                info.size = len(data)
                info.mode = 0o755 if path.suffix == '.sh' else 0o644
                archive.addfile(info, io.BytesIO(data))
        subprocess.run(ssh + [f'mkdir -p {REMOTE}/repo && tar xzf - -C {REMOTE}/repo'], input=buffer.getvalue(), check=True)
        print('SYNCED', len(files), 'files,', len(buffer.getvalue()) // 1024, 'KiB')
    else:
        subprocess.run(ssh + [f'cd {REMOTE} && rm -f results.tar.gz results.sha256 && '
                              "tar czf results.tar.gz --exclude='*.safetensors' runs && "
                              'sha256sum results.tar.gz > results.sha256'], check=True)
        expected = subprocess.check_output(ssh + [f'cat {REMOTE}/results.sha256']).decode().split()[0]
        RESULTS_LOCAL.mkdir(parents=True, exist_ok=True)
        archive_path = RESULTS_LOCAL / 'results.tar.gz'
        with archive_path.open('wb') as stream:
            subprocess.run(ssh + [f'cat {REMOTE}/results.tar.gz'], stdout=stream, check=True)
        if hashlib.sha256(archive_path.read_bytes()).hexdigest() != expected:
            raise SystemExit('Checksum mismatch; keeping the pod untouched')
        with tarfile.open(archive_path) as archive:
            for member in archive:
                destination = (RESULTS_LOCAL / member.name).resolve()
                if member.isdir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                if not member.isfile() or not destination.is_relative_to(RESULTS_LOCAL.resolve()):
                    raise SystemExit(f'Unsafe archive member: {member.name}')
                destination.parent.mkdir(parents=True, exist_ok=True)
                extracted = archive.extractfile(member)
                assert extracted is not None
                destination.write_bytes(extracted.read())
        print('VERIFIED and extracted to', RESULTS_LOCAL)


if __name__ == '__main__':
    main()
