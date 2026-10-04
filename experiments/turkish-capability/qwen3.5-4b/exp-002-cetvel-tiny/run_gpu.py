"""Detached evaluation/scoring/recovery coordinator; no training or credentials."""
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adapter', type=Path, required=True)
    parser.add_argument('--results-root', type=Path, required=True)
    args = parser.parse_args()
    support = Path('/workspace/cetvel-tiny-support')
    assert (support / 'setup-completed').exists()
    for arm in ('base', 'F'):
        probe = json.loads((Path('/workspace/cetvel-tiny-probe-v4') / arm / 'manifest.json').read_text())
        assert probe['status'] == 'completed' and probe['count'] == probe['native_eos_count'] == 2
    assert not args.results_root.exists(), 'Never restart/overwrite benchmark outputs'
    started = time.time()
    commands = [
        [sys.executable, str(HERE / 'evaluate_vllm.py'), '--adapter', str(args.adapter),
         '--output-dir', str(args.results_root)],
        [sys.executable, str(HERE / 'score_pair.py'), '--results-root', str(args.results_root)]]
    invocation = dict(python=sys.version, executable=sys.executable, platform=platform.platform(),
                      started_at_unix=started, commands=commands, wandb=False, training=False)
    (support / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
    for name, command in zip(('benchmark', 'scoring'), commands):
        with (support / (name + '.log')).open('w') as log:
            subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    invocation.update(completed_at_unix=time.time(), elapsed_seconds=time.time() - started)
    (support / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
    # Download this small archive, not the9GB base weights or already-recovered F.
    paths = []
    for folder in [args.results_root, support, Path('/workspace/cetvel-tiny-probe-v2'),
                   Path('/workspace/cetvel-tiny-probe-v3'), Path('/workspace/cetvel-tiny-probe-v4')]:
        if folder.exists():
            paths.extend(p for p in folder.rglob('*') if p.is_file())
    paths.extend(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths += [ROOT / 'scripts/evaluation/score_cetvel_generation.py',
              ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-015-target-quality-sft/evaluate_models.py']
    unique = sorted(set(paths))
    files = {str(p.relative_to('/workspace')): dict(bytes=p.stat().st_size,
             sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in unique}
    index = Path('/workspace/cetvel-tiny-backup-files.json')
    index.write_text(json.dumps(files, indent=2) + '\n')
    backup = Path('/workspace/cetvel-tiny-backup.tar.gz')
    with tarfile.open(backup, 'w:gz') as archive:
        for p in unique + [index]:
            archive.add(p, arcname=str(p.relative_to('/workspace')))
    result = dict(status='completed-remote-backup', file=backup.name, bytes=backup.stat().st_size,
                  sha256=hashlib.sha256(backup.read_bytes()).hexdigest(), count=200,
                  included_file_count=len(files), elapsed_seconds=invocation['elapsed_seconds'],
                  omission='Base weights downloadable by pinned revision; F already hash-recovered locally.')
    Path('/workspace/cetvel-tiny-backup.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
