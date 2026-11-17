"""Write bilingual-pilot-v01/release-manifest.json: hashes of every artifact, git state, freeze-order evidence."""
import datetime
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bilingual_pilot_common import BASE, PILOT, ROOT, json_bytes, sha256_file


def git(*a):
    return subprocess.run(['git', '-C', str(ROOT), *a], capture_output=True, text=True).stdout.strip()


def mtime(p):
    return datetime.datetime.fromtimestamp(p.stat().st_mtime, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def main():
    files = sorted(p for p in PILOT.rglob('*') if p.is_file() and p.name != 'release-manifest.json')
    scripts = sorted(ROOT.glob('scripts/datasets/*bilingual*.py')) + [ROOT / 'scripts/datasets/prepare_lfm3_bilingual_pilot_eval.py']
    exps = [BASE / 'exp-010-tr-only-sft160/config.yaml', BASE / 'exp-011-bilingual-sft640/config.yaml']
    ev = {p.name: mtime(p) for p in (PILOT / 'eval-v01').glob('*.jsonl')}
    tr = {p.name: mtime(p) for p in (PILOT / 'translations').glob('part-*.txt')}
    manifest = dict(
        status='prepared; validation passed; NOT trained, NOT published, NOT committed',
        git=dict(commit=git('rev-parse', 'HEAD'), dirty=bool(git('status', '--porcelain')), note='new files are uncommitted by instruction; builder commit must be recorded after owner approval'),
        freeze_order_evidence=dict(eval_manifest_frozen_at_utc=__import__('json').loads((PILOT / 'eval-v01/manifest.json').read_text(encoding='utf-8'))['frozen_at_utc'],
                                   eval_file_mtimes_utc=ev, translation_file_mtimes_utc=tr,
                                   note='mtimes are filesystem evidence only; eval files precede every translation part'),
        artifacts={p.relative_to(PILOT).as_posix(): sha256_file(p) for p in files},
        scripts={p.name: sha256_file(p) for p in scripts}, experiment_configs={p.parent.name: sha256_file(p) for p in exps})
    (PILOT / 'release-manifest.json').write_bytes(json_bytes(manifest))
    print(len(files), 'artifacts hashed')


if __name__ == '__main__':
    main()
