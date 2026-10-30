"""Create a small source/data ZIP for Colab; whitelist excludes secrets and weights."""
import argparse
import zipfile
import json
import subprocess
from pipeline import ROOT, DATA, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    paths = [ROOT/name for name in ('pipeline.py', 'train.py', 'evaluate.py', 'review.py', 'test_pipeline.py',
        'experiment-config.json', 'dev-prompts.jsonl', 'regression-prompts.jsonl', 'RUN.md')]
    paths += [DATA/name for name in ('authored-cases.tsv', 'train.jsonl', 'test-prompts.jsonl',
        'test-keys.jsonl', 'manifest.json')]
    with zipfile.ZipFile(args.output, 'x', zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, str(path.relative_to(ROOT)))
        provenance = dict(source_git_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            source_git_dirty=bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()),
            files_sha256={str(p.relative_to(ROOT)): sha(p) for p in paths},
            note='Bundle captures the listed current file bytes, including uncommitted edits; not a claim they match HEAD.')
        archive.writestr('source-provenance.json', json.dumps(provenance, indent=2)+'\n')
    from pathlib import Path
    print('Bundle SHA256:', sha(Path(args.output)))


if __name__ == '__main__':
    main()
