"""Generate both scheduled epoch checkpoints on unchanged development items."""
from pathlib import Path
import subprocess
import sys

ROOT=Path('/workspace/exp010-runs')
SCRIPT=Path(__file__).resolve().parent.parent/'exp-009-minimal-edit/evaluate_adapter.py'
result=ROOT/'full-v1/result.json'
import json
assert json.loads(result.read_text())['status']=='completed'
for epoch,step in [(1,10),(2,20)]:
    adapter=ROOT/f'full-v1/checkpoints/checkpoint-{step}'
    assert (adapter/'adapter_model.safetensors').exists()
    with Path(f'/workspace/exp010-validation-epoch{epoch}.log').open('x') as log:
        subprocess.run([sys.executable,'-u',str(SCRIPT),'--adapter',str(adapter),
            '--output-dir',str(ROOT/f'validation-epoch{epoch}-v1')],stdout=log,stderr=subprocess.STDOUT,check=True)
    print('Completed epoch',epoch,flush=True)
