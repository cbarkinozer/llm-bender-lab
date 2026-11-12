"""Verify actual pair completion; distinguish recovery integrity from quality."""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model-root', type=Path, required=True)
    p.add_argument('--verify-wandb', action='store_true')
    a = p.parse_args()
    load = lambda path: json.loads(path.read_text())
    lines = lambda path: [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]
    records = {}
    api = None
    if a.verify_wandb:
        os.environ['WANDB_API_KEY'] = Path('/workspace/.secrets/wandb-key').read_text().strip()
        import wandb
        api = wandb.Api(timeout=30)
    for name in ['exp-001-wiki-cpt', 'exp-002-mixed-cpt']:
        exp = a.model_root/name
        cfg = load(exp/'config-planned.json')
        root = exp/'results-local'
        train = root/'cpt-v01'
        report = load(train/'training-manifest.json')
        state = load(train/'trainer_state.json')
        representation = load(train/'training-representation.json')
        assert report['status'] == 'training_completed' and report['model'] == cfg['model']
        assert report['source_manifest_sha256'] == hashlib.sha256((exp/cfg['active_cpt_manifest']).read_bytes()).hexdigest()
        assert state['global_step'] == math.ceil(representation['packed_train_rows']/8)
        assert report['training']['epoch'] == 1.0
        assert math.isfinite(report['training']['train_loss'])
        assert load(train/'label-audit.json')['status'] == load(train/'gradient-audit.json')['status'] == 'passed'
        assert (train/'optimizer-scheduler-rng.pt').stat().st_size > 0
        adapter = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (train/'adapter').iterdir() if p.is_file()}
        assert 'adapter_config.json' in adapter and any(k.endswith('.safetensors') for k in adapter)
        merge = load(train/'merge-manifest.json')
        assert merge['status'] == 'merged' and math.isfinite(merge['max_abs_logit_difference'])
        for stage, count in [('train-smoke',1), ('overfit',1), ('train',1), ('after',4)]:
            commands = lines(root/'control'/(stage+'-commands.jsonl'))
            assert len(commands) == count and all(x['exit_code'] == 0 for x in commands)
        comparison = load(root/'comparison-v01.json')
        assert comparison['status'] == 'matched_comparison_completed'
        evaluation = root/'cpt-eval-v01'
        predictions = lines(evaluation/'cetvel/answers.jsonl')
        manifest = load(evaluation/'cetvel/manifest.json')
        assert manifest['status'] == 'completed' and manifest['count'] == len(predictions) == 500
        assert len({r['id'] for r in predictions}) == 500
        text = load(evaluation/'text/text-scores.json')
        for split in ['wiki_eval','web_eval']:
            values = text['results'][split]
            assert len(values['documents']) == len({r['id'] for r in values['documents']}) == 100
            assert math.isfinite(values['nll']) and values['nll'] > 0
        pairs = lines(evaluation/'turblimp/pairs.jsonl')
        assert len(pairs) == len({r['id'] for r in pairs}) == 1600
        assert all(math.isfinite(r[k]) for r in pairs for k in ['good_logprob','bad_logprob'])
        tracking = load(train/'wandb-run.json')
        if api:
            run = api.run(tracking['url'].split('wandb.ai/',1)[1].replace('/runs/','/'))
            artifacts = [dict(name=x.name,state=x.state,digest=x.digest) for x in run.logged_artifacts()]
            assert run.state == 'finished' and any(x['state'] == 'COMMITTED' for x in artifacts)
            tracking.update(verified_state=run.state, logged_artifacts=artifacts)
        exposures = lines(train/'token-exposure.jsonl')
        records[name] = dict(status='completed_and_checked', updates=state['global_step'],
            training=report['training'], peak_gpu_allocated_bytes=report['peak_gpu_allocated_bytes'],
            actual_label_token_exposure=sum(r['supervised_tokens'] for r in exposures),
            exposure_note='Count of nonmasked labels, before causal shift; not number of distinct documents or independent observations.',
            adapter_sha256=adapter, merge_probe={k:v for k,v in merge.items() if k!='files'},
            cetvel_count=500, text_documents=200, grammar_pairs=1600,
            termination=dict(Counter(r['finish_reason'] for r in predictions)),
            empty_predictions=sum(not r['prediction'].strip() for r in predictions),
            wandb=tracking)
    result = dict(status='pair_completion_verified', wandb_api_checked=bool(api), runs=records,
        caveat='Completion and adapter reload are verified; length/loop/timeout outputs remain in scores. Local archive integrity must be verified separately before shutting down the pod.')
    (a.model_root/'cpt-pair-completion-v01.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
