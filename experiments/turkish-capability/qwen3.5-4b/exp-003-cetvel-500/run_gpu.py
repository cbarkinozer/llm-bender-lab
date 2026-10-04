"""Run1000 outputs, score, paired analysis and archive all recovery evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SHARED = HERE.parent / 'exp-002-cetvel-tiny'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adapter', type=Path, required=True)
    parser.add_argument('--results-root', type=Path, default=Path('/workspace/cetvel-500-runs'))
    args = parser.parse_args()
    support = Path('/workspace/cetvel-500-support')
    assert (support / 'setup-completed').exists()
    assert args.results_root == Path('/workspace/cetvel-500-runs')
    assert not args.results_root.exists(), 'Never overwrite prior outputs'
    transfer_path = ROOT / 'cetvel-500-transfer-manifest.json'
    transfer = json.loads(transfer_path.read_text())
    for name, expected in transfer['source_hashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, ('Transferred source changed', name)
    commands = [
        [sys.executable, str(SHARED / 'evaluate_vllm.py'), '--experiment-dir', str(HERE),
            '--adapter', str(args.adapter), '--output-dir', str(args.results_root)],
        [sys.executable, str(SHARED / 'score_pair.py'), '--results-root', str(args.results_root)],
        [sys.executable, str(HERE / 'paired_analysis.py'), '--results-root', str(args.results_root)]]
    invocation = dict(python=sys.version, executable=sys.executable, platform=platform.platform(),
        started_at_unix=time.time(), commands=commands, wandb=False, training=False,
        git_commit=transfer['git_commit'], transfer_manifest_sha256=hashlib.sha256(transfer_path.read_bytes()).hexdigest(),
        extra_smoke_or_overfit=False)
    invocation_path = support / 'invocation.json'
    invocation_path.write_text(json.dumps(invocation, indent=2) + '\n')
    status = 'completed-remote-backup'
    try:
        for name, command in zip(('benchmark', 'scoring', 'paired-analysis'), commands):
            with (support / (name + '.log')).open('x') as log:
                subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    except Exception as exc:
        status = 'failed-remote-backup'
        invocation['failure'] = str(exc)
    invocation.update(completed_at_unix=time.time(), elapsed_seconds=time.time() - invocation['started_at_unix'], status=status)
    invocation_path.write_text(json.dumps(invocation, indent=2) + '\n')
    paths = []
    for folder in (args.results_root, support, HERE):
        if folder.exists():
            paths.extend(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths += [SHARED / n for n in ('evaluate_vllm.py', 'score_pair.py', 'verify_recovery.py')]
    paths += [transfer_path, ROOT / 'scripts/evaluation/score_cetvel_generation.py',
        ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-015-target-quality-sft/evaluate_models.py']
    paths = sorted(set(paths))
    files = {str(p.relative_to('/workspace')): dict(bytes=p.stat().st_size,
        sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths}
    index = Path('/workspace/cetvel-500-backup-files.json')
    index.write_text(json.dumps(files, indent=2) + '\n')
    archive_path = Path('/workspace/cetvel-500-backup.tar.gz')
    assert not archive_path.exists()
    with tarfile.open(archive_path, 'w:gz') as archive:
        for p in paths + [index]:
            archive.add(p, arcname=str(p.relative_to('/workspace')))
    metadata = dict(status=status, count=1000 if status == 'completed-remote-backup' else None,
        bytes=archive_path.stat().st_size, sha256=hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        included_file_count=len(files), elapsed_seconds=invocation['elapsed_seconds'],
        omission='Pinned base downloadable; final F already hash-recovered locally.')
    Path('/workspace/cetvel-500-backup.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(metadata), flush=True)
    if status != 'completed-remote-backup':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
