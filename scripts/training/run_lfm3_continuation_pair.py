"""Owner-approved serial 10M -> 50M -> 100M continuation; no time limit/inference."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import time


ROOT = Path('experiments/turkish-capability/lfm3-1.7b')
PY = '/workspace/.venvs/lfm3/bin/python'


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def digest(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def dump(p, value):
    p.write_text(json.dumps(value,indent=2)+'\n')


def run(command, log):
    start = time.time()
    with log.open('w') as out:
        result = subprocess.run([str(x) for x in command],stdout=out,stderr=subprocess.STDOUT)
    with (ROOT/'preparation-local/continuation-commands.jsonl').open('a') as out:
        out.write(json.dumps(dict(command=[str(x) for x in command],seconds=time.time()-start,
            started_unix=start,exit_code=result.returncode,log=str(log)))+'\n')
    if result.returncode:
        raise RuntimeError('Failed; preserve attempt: '+str(log))


def main():
    import os
    os.environ.update(HF_HOME='/workspace/.cache/huggingface',PYTHONUNBUFFERED='1',
        WANDB_API_KEY=Path('/workspace/.secrets/wandb-key').read_text().strip())
    source = ROOT/'preparation-local/continuation-90m-v05'
    manifest = read(source/'manifest.json')
    review = read(ROOT/'continuation-review-v01.json')
    assert review['status']=='accepted_for_exploratory_continuation'
    assert review['manifest_sha256']==digest(source/'manifest.json')
    assert review['sample_sha256']==digest(source/'review-sample.jsonl')
    assert digest(source/'wiki_train.jsonl')==manifest['splits']['wiki_train']['sha256']
    baseline = ROOT/'exp-000-baseline'
    parent_exp = ROOT/'exp-002-mixed-cpt'
    parent_config = read(parent_exp/'config-planned.json')
    parent_manifest = read(parent_exp/parent_config['active_cpt_manifest'])
    parent_tokens = parent_manifest['raw_tokens_no_eos']['combined']['tokens']
    parent_adapter = parent_exp/'results-local/cpt-v01/adapter'
    old_ids = set(parent_manifest['splits']['wiki_train']['ids'])
    groups, tokens, seen, texts = [[],[]], [0,0], set(), set()
    with (source/'wiki_train.jsonl').open(encoding='utf-8') as f:
        for line in f:
            row = json.loads(line)
            if not row['id'].startswith('fineweb-train-'):
                continue
            assert row['source_split']=='train' and row['source_revision']==manifest['web_revision']
            assert row['id'] not in old_ids and row['id'] not in seen
            assert row['normalized_text_sha256'] not in texts
            seen.add(row['id']);texts.add(row['normalized_text_sha256'])
            slot = 0 if tokens[0]<40_000_000 else 1
            groups[slot].append(row)
            tokens[slot] += row['lfm_raw_tokens']
    assert 90_000_000 <= sum(tokens) < 90_020_000
    assert 40_000_000 <= tokens[0] < 40_020_000
    audit = dict(source_manifest_sha256=digest(source/'manifest.json'),new_raw_tokens=tokens,
        new_documents=[len(g) for g in groups],distinct_new_ids=len(seen),
        distinct_normalized_texts=len(texts),parent_raw_tokens=parent_tokens,
        policy='Fresh FineWeb only after existing CPT-B. No replay of parent Wiki/web. Approximate milestones; EOS exposure recorded separately.')
    dump(ROOT/'continuation-data-audit-v01.json',audit)
    for slot, name in enumerate(['exp-003-cpt-cont-50m','exp-004-cpt-cont-100m']):
        exp = ROOT/name
        exp.mkdir(exist_ok=False)
        data = exp/'data-local/cpt-cont-v01'
        data.mkdir(parents=True)
        provenance = exp/'data-local/provenance'
        provenance.mkdir()
        for filename in ['manifest.json','review-sample.jsonl']:
            shutil.copy2(source/filename,provenance/filename)
        shutil.copy2('/workspace/setup-logs/continuation-data-v05.log',provenance/'selection.log')
        for filename in ['training-runtime.json','training-runtime.freeze.txt']:
            runtime = ROOT/'preparation-local/gpu-20261112'/filename
            if runtime.exists():
                shutil.copy2(runtime,provenance/filename)
        receipts = {}
        with (data/'wiki_train.jsonl').open('w',encoding='utf-8',newline='\n') as f:
            for row in groups[slot]:
                f.write(json.dumps(row,ensure_ascii=False)+'\n')
        receipts['wiki_train'] = dict(count=len(groups[slot]),sha256=digest(data/'wiki_train.jsonl'))
        original_manifest = read(baseline/'cpt-data-manifest-v02.json')
        for split in ['wiki_dev','wiki_eval','web_eval']:
            shutil.copy2(baseline/'data-local/cpt-v02'/(split+'.jsonl'),data/(split+'.jsonl'))
            receipts[split] = original_manifest['splits'][split]
        for filename in ['questions-500.jsonl','turblimp-1600.jsonl']:
            shutil.copy2(baseline/'data-local'/filename,exp/'data-local'/filename)
        for filename in ['cpt-data-manifest-v02.json','turblimp-manifest-v01.json','requirements-gpu.txt']:
            shutil.copy2(baseline/filename,exp/filename)
        alias = exp/'data-local/cpt-v02'
        alias.mkdir()
        for split in ['wiki_dev','wiki_eval','web_eval']:
            shutil.copy2(data/(split+'.jsonl'),alias/(split+'.jsonl'))
        dump(exp/'cpt-continuation-manifest-v01.json',dict(splits=receipts,raw_tokens=tokens[slot],
            source_manifest_sha256=audit['source_manifest_sha256'],review=review,protection=manifest['policy'],
            limitations=manifest['limitations'],source_revision=manifest['web_revision'],source_split='train'))
        cfg = json.loads(json.dumps(parent_config))
        for stale in ['training_order','independent_parent_for_each_arm']:
            cfg.pop(stale,None)
        cfg.update(experiment_id=name,parent=str(parent_exp),starting_checkpoint='Saved cumulative parent LoRA adapter',
            active_cpt_manifest='cpt-continuation-manifest-v01.json',active_cpt_data='data-local/cpt-cont-v01',
            cpt_train_split='wiki_train',parent_adapter_sha256=digest(parent_adapter/'adapter_model.safetensors'),
            status='GPU_DIAGNOSTICS_PENDING',gpu_ready=False,
            lineage=dict(parent_adapter=str(parent_adapter),parent_raw_tokens=parent_tokens,
                added_raw_tokens=tokens[slot],cumulative_raw_tokens=parent_tokens+tokens[slot],
                nominal_total_tokens=50_000_000 if slot==0 else 100_000_000,
                optimizer='fresh AdamW each continuation phase, not resuming the exhausted parent scheduler',
                schedule='independent phase-local warmup5% + cosine decay, peak1e-4; not uninterrupted100M',
                data_mix='new FineWeb prose only; cumulative Wiki share decreases',
                hard_training_time_limit=None))
        cfg['training'].update(learning_rate=1e-4,save_steps=200,save_total_limit=2)
        cfg['tracking']['group']='lfm3-turkish-cpt-continuation-50m-100m-v01'
        cfg['cpt_run_label']=f'lfm3-1.7b-cpt-cont-to{50 if slot==0 else 100}m-web-r64-lr1e-4-1ep-s3407'
        dump(exp/'config-planned.json',cfg)
        shutil.copy2(exp/'config-planned.json',exp/'config.yaml')
        (exp/'README.md').write_text('# '+name+'\n\nContinuation from '+str(parent_exp)+
            '. Fresh phase-local AdamW/cosine schedule, peak LR1e-4, warmup5%, rank64; embeddings frozen.\n'+
            'Milestones are nominal cumulative raw-token budgets; exact raw and EOS/packed exposure are recorded.\n'+
            'New FineWeb prose only, no parent-corpus replay. Not an uninterrupted100M run.\n'+
            'Resumable checkpoints every200 optimizer updates, keep last2. No automatic time limit.\n'+
            'Inference postponed by owner; no benchmark run is scheduled.\n')
        results = exp/'results-local'
        results.mkdir()
        for mode, extra in [('smoke',['--smoke']),('overfit',['--tiny-overfit'])]:
            output = results/('cpt-smoke-v01' if mode=='smoke' else 'cpt-overfit-v01')
            run([PY,'scripts/training/train_lfm3_cpt_continuation.py','--experiment-dir',exp,
                '--parent-adapter',parent_adapter,'--output-dir',output]+extra,results/(mode+'.log'))
        reports = [read(results/f/'training-manifest.json') for f in ['cpt-smoke-v01','cpt-overfit-v01']]
        for folder, expected in [('cpt-smoke-v01',2),('cpt-overfit-v01',30)]:
            p = results/folder
            assert read(p/'trainer_state.json')['global_step']==expected
            assert read(p/'label-audit.json')['status']==read(p/'gradient-audit.json')['status']=='passed'
            assert read(p/'training-manifest.json')['parent_adapter_sha256']==cfg['parent_adapter_sha256']
        assert reports[1]['development']['eval_loss'] < reports[1]['initial_evaluation']['eval_loss']*.98
        assert all(r['peak_gpu_allocated_bytes'] < 24_564*1024**2 for r in reports)
        assert read(baseline/'results-local/base-v01/cetvel/manifest.json')['status']=='completed'
        dump(exp/'data-local/gpu-gate.json',dict(baseline_completed=True,training_smoke_passed=True,
            labels_audited=True,tiny_overfit_passed=True,model_revision=cfg['model']['revision'],
            parent_adapter_sha256=cfg['parent_adapter_sha256'],data_manifest_sha256=digest(exp/cfg['active_cpt_manifest']),
            diagnostic_manifest_hashes=[digest(results/f/'training-manifest.json') for f in ['cpt-smoke-v01','cpt-overfit-v01']]))
        run([PY,'scripts/training/train_lfm3_cpt_continuation.py','--experiment-dir',exp,
            '--parent-adapter',parent_adapter,'--output-dir',results/'cpt-v01'],results/'training.log')
        training = read(results/'cpt-v01/training-manifest.json')
        assert training['status']=='training_completed' and training['training']['epoch']==1.0
        assert read(results/'cpt-v01/gradient-audit.json')['status']=='passed'
        with (exp/'README.md').open('a') as f:
            f.write('\nTraining completed; W&B run: '+read(results/'cpt-v01/wandb-run.json')['url']+
                '. Full results/optimizer states are in results-local/cpt-v01. Inference pending.\n')
        # Stage-level recovery leaves the two most recent Trainer checkpoints resumable.
        archive = Path('/workspace')/('lfm3-'+name+'-20261112.tar.gz')
        files = sorted(p for p in exp.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
        files += list(Path('scripts/training').glob('*lfm3*.py'))+list(Path('scripts/datasets').glob('*lfm3*.py'))
        files += [ROOT/'continuation-data-audit-v01.json',ROOT/'continuation-review-v01.json']
        receipt = {str(p):digest(p) for p in files}
        assert not archive.exists()
        with tarfile.open(archive,'w:gz',compresslevel=1,dereference=True) as tar:
            for p in files: tar.add(p,arcname=str(p),recursive=False)
        dump(archive.with_suffix(archive.suffix+'.json'),dict(archive_sha256=digest(archive),files=receipt,
            archive_bytes=archive.stat().st_size,training_manifest=training,status='milestone_training_completed_inference_pending'))
        print('MILESTONE_READY '+name,flush=True)
        parent_exp, parent_adapter = exp, results/'cpt-v01/adapter'
        parent_tokens += tokens[slot]
    print('CONTINUATION_PAIR_TRAINING_COMPLETED',flush=True)


if __name__=='__main__':
    main()
