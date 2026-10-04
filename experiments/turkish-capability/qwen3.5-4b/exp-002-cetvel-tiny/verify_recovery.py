"""Verify archive/file/arm hashes and prompt parity before GPU is disposable."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile

from score_pair import load


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--extract-root', type=Path, required=True)
    parser.add_argument('--bundle-prefix', default='cetvel-tiny')
    args = parser.parse_args()
    metadata = json.loads(args.metadata.read_text())
    assert args.archive.stat().st_size == metadata['bytes']
    assert sha(args.archive) == metadata['sha256']
    root = args.extract_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.archive) as archive:
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            assert member.isfile() and not path.is_absolute() and '..' not in path.parts
            target = (root / member.name).resolve()
            assert target.is_relative_to(root)
            if target.exists():
                assert target.read_bytes() == archive.extractfile(member).read(), target
        archive.extractall(root)
    files = json.loads((root / (args.bundle_prefix + '-backup-files.json')).read_text())
    assert len(files) == metadata['included_file_count']
    for name, expected in files.items():
        target = root / name
        assert target.stat().st_size == expected['bytes'] and sha(target) == expected['sha256'], name
    results = root / (args.bundle_prefix + '-runs')
    bm, base = load(results / 'base')
    fm, adapted = load(results / 'F')
    assert metadata['status'] == 'completed-remote-backup'
    assert len(base) + len(adapted) == metadata['count']
    for key in ('config', 'questions_sha256', 'packages', 'backend', 'precision',
                'chat_template_sha256', 'eos_token_ids', 'source_hashes'):
        assert bm[key] == fm[key], key
    for a, b in zip(base, adapted):
        for key in ('id', 'task', 'document', 'target', 'semantic_prompt', 'rendered_prompt', 'prompt_token_ids'):
            assert a[key] == b[key], (a['id'], key)
    assert (results / 'comparison.json').exists()
    report = dict(status='verified-local-recovery-pod-can-be-closed',
                  archive_sha256=sha(args.archive), files_verified=len(files), count=metadata['count'],
                  prompt_parity=True, base_native_eos=bm['native_eos_count'], F_native_eos=fm['native_eos_count'],
                  F_adapter_hashes=fm['adapter_hashes'], human_review_pending=True,
                  scope='All inference/config/code/logs/scoring; F weights already verified locally; base revision pinned.')
    (root / 'local-recovery-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
