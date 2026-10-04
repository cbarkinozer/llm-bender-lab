"""Create narrow source and F-adapter transfer archives; no secrets or venvs."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--adapter', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    archives = {}
    source = args.output_dir / 'cetvel-tiny-source.tar.gz'
    files = [p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    files += [ROOT / 'scripts/evaluation/score_cetvel_generation.py', ROOT / 'AGENTS.md']
    pair = ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-015-target-quality-sft'
    files += [pair / 'evaluate_models.py']
    with tarfile.open(source, 'w:gz') as archive:
        for path in files:
            assert path.suffix not in ('.env', '.bin', '.safetensors')
            archive.add(path, arcname=path.relative_to(ROOT).as_posix())
    adapter = args.output_dir / 'F-adapter.tar.gz'
    config = json.loads((HERE / 'config.json').read_text())
    with tarfile.open(adapter, 'w:gz') as archive:
        for name, expected in config['adapter_hashes'].items():
            path = args.adapter / name
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
            archive.add(path, arcname='F-adapter/' + name)
    for path in (source, adapter):
        archives[path.name] = dict(bytes=path.stat().st_size,
                                  sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    (args.output_dir / 'transfer-manifest.json').write_text(json.dumps(archives, indent=2) + '\n')
    print(json.dumps(archives))


if __name__ == '__main__':
    main()
