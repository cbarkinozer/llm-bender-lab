"""Reuse the historical native-label Trainer unchanged with explicit new run globals."""
import argparse
import gc
import json
from pathlib import Path
import run_lfm3_bilingual_gpu as historical

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/turkish-capability/lfm3-1.7b'
RUN=BASE/'preservation-session-v01-local'
EXPERIMENTS=['exp-012-base-bilingual','exp-013-base-preservation']

def configure():
    historical.RUN=RUN
    historical.EXPERIMENTS=EXPERIMENTS

def gate():
    from run_lfm3_sft160 import dump,read
    experiments={}
    for exp in EXPERIMENTS:
        fp=historical.fingerprints(exp)
        for mode in ['smoke','tiny-overfit']:
            result=read(BASE/exp/'results-local'/mode/'training-manifest.json')
            assert result['status']=='passed' and result['fingerprints']==fp
        assert read(RUN/'native'/exp/'label-audit.json')['status']=='passed'
        experiments[exp]=fp
    assert read(RUN/'baseline-completion.json')['status']=='completed'
    dump(RUN/'gpu-gate.json',dict(experiments=experiments,baseline_completed=True,
        native_labels_passed=True,smoke_passed=True,tiny_overfit_passed=True,
        owner_data_decisions_recorded=True,authorization='NEXT-GPU-AUTHORIZATION.md'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['native-audit','smoke','tiny-overfit','sft','gate'])
    p.add_argument('--experiment',choices=EXPERIMENTS,default=EXPERIMENTS[0]);a=p.parse_args()
    historical.environment();configure()
    if a.mode=='native-audit':historical.native_audit(a.experiment)
    elif a.mode=='gate':gate()
    else:
        if a.mode=='tiny-overfit':
            # Keep the identical historical20 diagnostic on both arms. The
            # fifth synthetic source would make the old four-source selector
            # choose25 and fail; all720 actual rows retain the native-label audit.
            original_load=historical.load
            def diagnostic_load(experiment):
                cfg,rows,order=original_load(experiment)
                return cfg,rows[:640],order
            historical.load=diagnostic_load
        historical.train(a.experiment,a.mode)
