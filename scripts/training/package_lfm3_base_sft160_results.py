"""Pod-side adapter-only and small-result archives; never include full weights or secrets."""
import hashlib
import argparse
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'experiments/turkish-capability/lfm3-1.7b'
EXP = BASE/'exp-009-base-sft160-lr1e4'
RUNTIME = BASE/'base-sft160-runtime-local'


def package(name, files):
    destination = Path('/workspace')/(name+'.tar.gz')
    manifest_path = destination.with_name(name+'-manifest.json')
    if destination.exists():
        assert manifest_path.exists(), 'Preserve incomplete archive for inspection'
        previous = json.loads(manifest_path.read_text())
        assert previous['files'] == {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        with destination.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == previous['sha256']
        print(json.dumps(dict(archive=str(destination), reused_verified=True)))
        return
    hashes = {}
    with tarfile.open(destination, 'w:gz') as tar:
        for p in sorted(files):
            assert p.is_file() and not p.is_symlink()
            relative = p.relative_to(ROOT).as_posix()
            assert '.env' not in p.name and 'private' not in relative.lower()
            assert not any(s in relative for s in ['optimizer.pt', 'rng_state.pth', 'scheduler.pt', 'merged-model', 'merged-step', '/init-model/'])
            data = p.read_bytes()
            hashes[relative] = hashlib.sha256(data).hexdigest()
            info = tarfile.TarInfo(relative)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    chunk_size = 4*1024*1024
    parts = []
    with destination.open('rb') as stream:
        while data := stream.read(chunk_size):
            parts.append(dict(name=f'part-{len(parts):04d}.bin', bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    with destination.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    manifest = dict(archive=str(destination), bytes=destination.stat().st_size, sha256=digest,
                    files=hashes, chunk_size=chunk_size, parts=parts,
                    excludes='Full/merged weights, optimizer/resume states, credentials and private keys')
    destination.with_name(name+'-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(dict(archive=str(destination), bytes=manifest['bytes'], sha256=digest, files=len(hashes))))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adapters-only', action='store_true')
    args = parser.parse_args()
    if not args.adapters_only:
        assert json.loads((RUNTIME/'completion.json').read_text())['status'] == 'completed-pending-owner-review'
    small = {p for p in RUNTIME.rglob('*') if p.is_file()
             and 'init-model' not in p.parts and p.stat().st_size < 30_000_000}
    small.update(p for p in (EXP/'results-local/sft').glob('*.json'))
    small.update(p for p in (EXP/'results-local').glob('*/training-manifest.json'))
    small.update(p for p in (EXP/'results-local').glob('*/wandb-run.json'))
    small.update([EXP/'config.yaml', EXP/'README.md'])
    # Exclude any future private Argilla keys from portable result packages.
    small = {p for p in small if 'private' not in p.as_posix().lower() and not any(x.startswith('argilla') for x in p.parts)}
    if not args.adapters_only:
        package('base-sft160-results', small)
    adapters = set()
    allowed = {'adapter_model.safetensors', 'adapter_config.json', 'tokenizer.json', 'tokenizer_config.json',
               'special_tokens_map.json', 'chat_template.jinja', 'README.md', 'added_tokens.json',
               'vocab.json', 'merges.txt', 'generation_config.json', 'trainer_state.json', 'training_args.bin'}
    for step in [60,100]:
        folder = EXP/'results-local/sft'/f'checkpoint-{step}'
        assert (folder/'adapter_model.safetensors').is_file()
        adapters.update(p for p in folder.iterdir() if p.is_file() and p.name in allowed)
    package('base-sft160-loras', adapters)


if __name__ == '__main__':
    main()
