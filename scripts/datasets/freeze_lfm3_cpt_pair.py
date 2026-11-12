"""Create complete experiment configs and private data copies after web preparation."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--model-dir',type=Path,required=True)
    a=p.parse_args(); root=a.model_dir; baseline=root/'exp-000-baseline'
    mixed=baseline/'data-local/cpt-mixed-10m-v05'
    manifest=json.loads((mixed/'manifest.json').read_text())
    review=json.loads((root/'cpt-pair-sample-review-v01.json').read_text())
    if review['status']!='accepted_for_exploratory_pilot' or review['sample_sha256']!=hashlib.sha256((mixed/'review-sample.jsonl').read_bytes()).hexdigest():
        raise ValueError('Missing/stale sample review')
    cfg=json.loads((baseline/'config-planned.json').read_text())
    recipe=dict(method='lora-cpt',precision='bfloat16',quantization=None,
        epochs=1,micro_batch_size=2,gradient_accumulation_steps=4,learning_rate=2e-4,
        scheduler='cosine',warmup_fraction=.05,max_length=2048,packing=True,
        packing_strategy='wrapped',loss='all nonpadding text tokens; raw text, no chat template',
        lora_rank=64,lora_alpha=64,lora_dropout=0,
        target_modules=['q_proj','k_proj','v_proj','o_proj','in_proj','out_proj','w1','w2','w3'],
        embeddings_trainable=False,seed=3407,checkpoint_selection='last completed epoch; no benchmark selection')
    recipe.update(optimizer='adamw_torch_fused',weight_decay=0.,adam_beta1=.9,
        adam_beta2=.999,adam_epsilon=1e-8,max_grad_norm=1.,gradient_checkpointing=True,
        dataloader_num_workers=0)
    for name,label in [('exp-001-wiki-cpt','wiki-2m2'),('exp-002-mixed-cpt','wiki-fineweb-10m')]:
        exp=root/name
        if exp.exists(): raise ValueError('Refusing overwrite: '+str(exp))
        exp.mkdir()
        c=json.loads(json.dumps(cfg));c.update(status='CPU_PREPARED_GPU_GATES_PENDING',
            experiment_id=name,parent='exp-000-baseline',starting_checkpoint='original pinned model; independent adapters',
            training=recipe,cpt_run_label=f'lfm3-1.7b-cpt-{label}-r64-lr2e-4-1ep-s3407',
            sample_review='../cpt-pair-sample-review-v01.json',
            active_cpt_manifest='cpt-data-manifest-v02.json',active_cpt_data='data-local/cpt-v02',
            pending=['actual GPU smoke, actual labels and tiny-overfit','training and matched evaluation'])
        c['tracking']['group']='lfm3-turkish-cpt-pair-v01'
        c['gpu_ready']=False
        c['gpu_ready_scope']='CPU data/configs prepared; GPU diagnostics must pass separately for each manifest'
        shutil.copytree(baseline/'data-local/cpt-v02',exp/'data-local/cpt-v02')
        for file in ('questions-500.jsonl','turblimp-1600.jsonl'):
            shutil.copy2(baseline/'data-local'/file,exp/'data-local'/file)
        for file in ('cpt-data-manifest-v02.json','turblimp-manifest-v01.json','requirements-gpu.txt'):
            shutil.copy2(baseline/file,exp/file)
        if name=='exp-002-mixed-cpt':
            shutil.copytree(mixed,exp/'data-local/cpt-mixed-10m-v05')
            shutil.copy2(mixed/'manifest.json',exp/'cpt-mixed-manifest-v05.json')
            c.update(active_cpt_manifest='cpt-mixed-manifest-v05.json',active_cpt_data='data-local/cpt-mixed-10m-v05')
        c['evaluation']=dict(baseline_directory='../exp-000-baseline',reuse_existing_baseline=True,
            primary='held-out Wikipedia and FineWeb raw-text NLL, separately',
            supporting=['TurBLiMP1600','CETVEL500 task metrics','generation length and termination'],
            caveats=['single-seed exploratory','quantity and source mix change together',
                'no English retention claim; no matched English baseline','CETVEL previously inspected comparison cohort'])
        payload=json.dumps(c,indent=2)+'\n'
        (exp/'config-planned.json').write_text(payload)
        # JSON is a YAML subset. Identical bytes prevent differing shadow recipes.
        (exp/'config.yaml').write_text(payload)
        (exp/'README.md').write_text(f'''# {name}

Status: planned; CPU inputs frozen, GPU smoke/labels/tiny-overfit pending.

Parent/comparison: exp-000-baseline. Start independently from the pinned original
LiquidAI/LFM3-1.7B; never continue from the other CPT adapter.

Hypothesis: {'2.202M clean Wikipedia tokens improve held-out Turkish language modeling.' if name=='exp-001-wiki-cpt' else 'Adding approximately 7.798M filtered web tokens to the identical Wikipedia set improves the broader Turkish adaptation recipe.'}

Complete recipe: config.yaml, byte-identical to runner input config-planned.json.
Shared implementation: scripts/training/train_lfm3_cpt.py. This first recipe keeps
embeddings frozen, one epoch, rank64, LR2e-4, raw-text all-token loss, 2048 packing.

Evaluate final epoch against the existing baseline with the frozen protocol.
Report NLL separately by source, grammar, each task score, answer lengths and
termination. No pooled score, no English preservation claim, no automatic selection.
The pair changes quantity and source composition, not a causal source-only ablation.

Results/conclusion: not run. See ../CPT-PAIR-TODO-20261112.md for launch and recovery.
''')
    receipt=dict(status='CPU_frozen_GPU_gates_pending',mixed_manifest_sha256=hashlib.sha256((mixed/'manifest.json').read_bytes()).hexdigest(),
        experiments=['exp-001-wiki-cpt','exp-002-mixed-cpt'],raw_tokens=manifest['raw_tokens_no_eos'])
    (root/'cpt-pair-preparation-v01.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__': main()
