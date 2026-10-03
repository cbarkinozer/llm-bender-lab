"""Explicit user waiver: mark skipped checks as skipped, not newly passed."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=Path('/workspace/exp010-runs')
result=json.loads((ROOT/'representation-v1/result.json').read_text())
mask=json.loads((ROOT/'representation-v1/mask-check.json').read_text())
assert result['status']=='passed' and mask['all_rows_verified'] and mask['trainable_parameters']>0
report=json.loads((HERE/'preparation-report.json').read_text())
assert report['training_changes']==['learning_rate'] and report['unchanged_dataset'] and report['unchanged_tokenized_data']
gate=dict(training_config_sha256=hashlib.sha256((HERE/'training-preflight-v1/training-config.json').read_bytes()).hexdigest(),
    actual_batch_masking=True,smoke_finite_loss=False,adapter_save_reload=False,tiny_overfit_loss_decreased=False,wandb_connected=False,
    policy='explicit-user-approved-lr-only-waiver',waived_checks=['smoke_finite_loss','adapter_save_reload','tiny_overfit_loss_decreased'],
    reason='User explicitly requested skipping repeated smoke and tiny-overfit for LR-only change on 2026-10-03. New environment imports/CUDA and actual batch masks passed. Smoke already in progress was interrupted; no new smoke/tiny pass claimed.',
    parent_evidence=dict(experiment='exp-009-minimal-edit',smoke_loss=1.7343841393788655,reload_loss=0.6162181496620178,tiny_before=0.4482119679450989,tiny_after=0.0004388985107652843),
    evidence=dict(trainable_parameters=mask['trainable_parameters']))
with (ROOT/'gpu-gates.json').open('x') as f:
    json.dump(gate,f,indent=2)
print(json.dumps(gate))
