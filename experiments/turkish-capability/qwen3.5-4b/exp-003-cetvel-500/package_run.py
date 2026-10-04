"""Narrow, hashed source bundle; reuse recovered F archive; no keys/env/weights in Git."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SHARED = HERE.parent / 'exp-002-cetvel-tiny'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / 'cetvel-500-source.tar.gz'
    assert not path.exists(), 'Preserve prior bundle; use a fresh run directory'
    files = [p for p in HERE.iterdir() if p.is_file() and p.suffix in ('.py', '.sh', '.md', '.json')]
    files += list((HERE / 'data-v1').glob('*.json')) + list((HERE / 'data-v1').glob('*.jsonl'))
    files += [SHARED / n for n in ('evaluate_vllm.py', 'score_pair.py', 'verify_recovery.py', 'import_human_review.py')]
    files += [ROOT / 'AGENTS.md', ROOT / 'scripts/evaluation/score_cetvel_generation.py',
        ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-015-target-quality-sft/evaluate_models.py']
    sources = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    manifest = dict(git_commit=commit, working_tree_sources=True, source_hashes=sources,
        note='Narrow exact source snapshot includes uncommitted files; commit alone is not the executed code identity.')
    manifest_path = args.output_dir / 'transfer-manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    with tarfile.open(path, 'w:gz') as archive:
        for p in files:
            archive.add(p, arcname=p.relative_to(ROOT).as_posix())
        archive.add(manifest_path, arcname='cetvel-500-transfer-manifest.json')
    report = dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        file=path.name, source_count=len(files))
    (args.output_dir / 'source-archive.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
