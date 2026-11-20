#!/usr/bin/env bash
set -euo pipefail
project=/workspace/reflex-decision
archive=/workspace/reflex-decision-artifacts-20261013.tar.gz
hf_archive=/workspace/hf-hub-cache-20261013.tar.gz

# Fail before archiving if any included file contains the copied W&B secret.
python - <<'PY'
from pathlib import Path
import os

root = Path('/workspace/reflex-decision')
secret = None
for line in (root / '.env').read_text().splitlines():
    if line.startswith('WANDB_API_KEY='):
        secret = line.partition('=')[2].strip().strip('"\'').encode()
if not secret:
    raise SystemExit('WANDB_API_KEY was not found; inspect credential handling')
hits = []
for scan_root in (root, Path('/root/.cache/huggingface/hub')):
    for base, dirs, files in os.walk(scan_root):
        dirs[:] = [d for d in dirs if d not in {'.venv', 'cache', 'unsloth_compiled_cache'}]
        for name in files:
            path = Path(base) / name
            if path == root / '.env' or path.is_symlink():
                continue
            try:
                with path.open('rb') as stream:
                    tail = b''
                    while chunk := stream.read(1 << 20):
                        if secret in tail + chunk:
                            hits.append(str(path))
                            break
                        tail = chunk[-len(secret) + 1:]
            except OSError:
                continue
if hits:
    raise SystemExit('Credential occurs in included file(s): ' + ', '.join(hits))
print('Credential scan passed')
PY

tar --exclude='reflex-decision/.env' \
    --exclude='reflex-decision/.venv' \
    --exclude='reflex-decision/cache' \
    --exclude='reflex-decision/unsloth_compiled_cache' \
    -czf "$archive" -C /workspace reflex-decision
sha256sum "$archive"
du -h "$archive"

tar -czf "$hf_archive" -C /root/.cache/huggingface hub
sha256sum "$hf_archive"
du -h "$hf_archive"
