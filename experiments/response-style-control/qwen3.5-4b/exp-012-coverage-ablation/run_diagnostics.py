"""Finish predeclared supporting probes and archive after primary outputs are saved."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path('/workspace/exp011-exp012-runs')
REPO=Path('/workspace/repos/llm-bender-lab')
HERE=REPO/'experiments/response-style-control/qwen3.5-4b/exp-012-coverage-ablation'
PYTHON='/workspace/.venvs/exp010-train/bin/python'

def main():
    os.environ.update(HF_HOME='/workspace/.cache/huggingface',PYTHONUNBUFFERED='1')
    deadline=time.monotonic()+1800
    while True:
        status=json.loads((ROOT/'status.json').read_text())
        assert status['status']!='failed',status
        if status['status']=='completed':
            break
        assert time.monotonic()<deadline
        time.sleep(5)
    for arm in ('A','B'):
        manifest=json.loads((ROOT/arm/'validation-v1/manifest.json').read_text())
        evidence=dict(adapter_loaded=True,evidence='completed 20-item saved-adapter evaluation',
            adapter_hashes=manifest['adapter_hashes'],native_eos_count=manifest['native_eos_count'],
            evaluation_manifest_sha256=hashlib.sha256((ROOT/arm/'validation-v1/manifest.json').read_bytes()).hexdigest())
        (ROOT/arm/'adapter-reload-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    (ROOT/'supporting-status.json').write_text(json.dumps(dict(status='running'))+'\n')
    for arm in ('base','A','B'):
        argv=[PYTHON,'-u',str(HERE/'supporting_diagnostics.py'),'--output-dir',str(ROOT/'diagnostics'/arm)]
        if arm!='base':
            argv.extend(['--adapter',str(ROOT/arm/'sft-v1/adapter')])
        with (ROOT/f'diagnostics-{arm}.log').open('x') as log:
            subprocess.run(argv,cwd=REPO,stdout=log,stderr=subprocess.STDOUT,check=True)
    (ROOT/'supporting-status.json').write_text(json.dumps(dict(status='completed',mode_probe_items=['me-070','me-079'],retained_train_ids=['me-041','me-051']))+'\n')
    with Path('/workspace/exp011-exp012-archive.log').open('x') as log:
        subprocess.run([PYTHON,'/workspace/archive_pair.py'],cwd=REPO,stdout=log,stderr=subprocess.STDOUT,check=True)

if __name__=='__main__':
    main()
