"""GPU-only explicit-label LoRA runner. Generation runs in a separate process."""
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent

def training_plan(config, mode):
    """Explicit step/row settings; preserve original defaults for old configs."""
    t=config['training']; d=config['dataset']
    counts={s:d.get(s+'_rows',80 if s=='train' else 20) for s in ('train','validation')}
    if any(not isinstance(n,int) or isinstance(n,bool) or n<=0 for n in counts.values()):
        raise ValueError('Configured split counts must be positive integers')
    steps=t.get('max_steps',-1)
    if not isinstance(steps,int) or isinstance(steps,bool) or (steps<=0 and steps!=-1):
        raise ValueError('max_steps must be -1 (epochs) or a positive integer')
    if mode=='full' and d.get('review_required',False):
        raise ValueError('Human-reviewed freeze is required before full training')
    if steps>0 and t.get('expected_optimizer_steps',steps)!=steps:
        raise ValueError('Explicit step budget disagrees with expected_optimizer_steps')
    save_strategy=t.get('save_strategy','epoch')
    eval_strategy='no' if mode!='full' else t.get('eval_strategy','epoch')
    kwargs={}
    for strategy,key in ((save_strategy,'save_steps'),(eval_strategy,'eval_steps')):
        if strategy=='steps':
            n=t.get(key)
            if not isinstance(n,int) or isinstance(n,bool) or n<=0:
                raise ValueError(key+' required for step strategy')
            kwargs[key]=n
    return dict(counts=counts,max_steps=3 if mode=='smoke' else 40 if mode=='tiny-overfit' else steps,
                save_strategy=save_strategy,eval_strategy=eval_strategy,step_kwargs=kwargs)

def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def collate_explicit(features,pad_id):
    """Pure-Python right padding; never rebuild or overwrite target labels."""
    width=max(len(f['input_ids']) for f in features)
    batch={k:[] for k in ('input_ids','labels','attention_mask')}
    for f in features:
        padding=width-len(f['input_ids'])
        batch['input_ids'].append(f['input_ids']+[pad_id]*padding)
        batch['labels'].append(f['labels']+[-100]*padding)
        batch['attention_mask'].append(f['attention_mask']+[0]*padding)
    return batch

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=['representation-check','smoke','tiny-overfit','full'],required=True)
    p.add_argument('--preflight-dir',type=Path,default=HERE/'training-preflight-v1')
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--gates',type=Path,help='Manually reviewed GPU gate file; required for full')
    args=p.parse_args()
    config=json.loads((args.preflight_dir/'training-config.json').read_text(encoding='utf-8'))
    plan=training_plan(config,args.mode)
    experiment_id=config['experiment_id']
    if args.mode=='full':
        os.environ.setdefault('WANDB_PROJECT','llm-bender-lab-response-style-control')
        os.environ.setdefault('WANDB_RUN_GROUP',experiment_id)
    report=json.loads((args.preflight_dir/'report.json').read_text(encoding='utf-8'))
    assert report['status']=='local-preflight-passed'
    for name,expected in report['files'].items():
        assert hashlib.sha256((args.preflight_dir/name).read_bytes()).hexdigest()==expected, name
    if args.output_dir.exists():
        raise ValueError('Refusing to overwrite GPU run')
    git=subprocess.check_output(['git','status','--porcelain'],cwd=HERE,text=True)
    if git.strip():
        raise ValueError('Commit experiment source before GPU execution')
    if args.mode=='full':
        if args.gates is None:
            raise ValueError('Full run requires reviewed GPU smoke/overfit/reload/W&B gates')
        gate=json.loads(args.gates.read_text(encoding='utf-8'))
        expected_hash=hashlib.sha256((args.preflight_dir/'training-config.json').read_bytes()).hexdigest()
        assert gate['training_config_sha256']==expected_hash
        for key in ('actual_batch_masking','smoke_finite_loss','adapter_save_reload','tiny_overfit_loss_decreased','wandb_connected'):
            if gate[key] is not True:
                policy=gate.get('policy')
                assert policy in ('explicit-user-approved-lr-only-waiver','explicit-user-approved-paired-run-waiver','explicit-user-approved-targeted-pair-waiver','explicit-user-approved-EF-smoke-tiny-waiver')
                if policy=='explicit-user-approved-EF-smoke-tiny-waiver':
                    assert experiment_id in ('exp-015-target-quality-sft','exp-016-diverse-coverage-sft')
                    assert gate.get('experiment_id')==experiment_id and gate.get('user_instruction')
                    assert key in ('smoke_finite_loss','tiny_overfit_loss_decreased')
                if policy=='explicit-user-approved-targeted-pair-waiver':
                    assert experiment_id in ('exp-013-targeted-coverage-sft','exp-014-targeted-duration-sft')
                    assert gate.get('experiment_id')==experiment_id and gate.get('user_instruction')
                if policy=='explicit-user-approved-paired-run-waiver':
                    assert experiment_id in ('exp-011-duration-ablation','exp-012-coverage-ablation')
                    assert gate.get('experiment_id')==experiment_id and gate.get('user_instruction')
                assert key in gate.get('waived_checks',[]) and key in ('smoke_finite_loss','adapter_save_reload','tiny_overfit_loss_decreased'),key
    from unsloth import FastLanguageModel
    import torch
    from datasets import Dataset
    from transformers import AutoTokenizer, Trainer, TrainingArguments, set_seed
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise ValueError('BF16-capable GPU required')
    args.output_dir.mkdir(parents=True)
    t=config['training']; m=config['model']; l=t['lora']
    set_seed(t['seed'])
    save(args.output_dir/'source-config.json',config)
    save(args.output_dir/'environment.json',dict(packages={n:importlib.metadata.version(n) for n in ['torch','transformers','unsloth','datasets','peft','accelerate']},cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(),git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip(),mode=args.mode))
    model,processor=FastLanguageModel.from_pretrained(model_name=m['name'],revision=m['revision'],max_seq_length=t['max_seq_length'],load_in_4bit=False,load_in_16bit=True,full_finetuning=False)
    model=FastLanguageModel.get_peft_model(model,r=l['rank'],lora_alpha=l['alpha'],lora_dropout=l['dropout'],bias=l['bias'],target_modules=l['target_modules'],use_gradient_checkpointing='unsloth',random_state=t['seed'])
    tokenizer=AutoTokenizer.from_pretrained(m['name'],revision=m['revision'])
    from prepare_training import encode_final
    processed={}
    for split in ('train','validation'):
        source=HERE/config['dataset'][split]
        assert hashlib.sha256(source.read_bytes()).hexdigest()==config['dataset']['hashes'][f'{split}-reviewed.jsonl']
        rows=[json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
        for r in rows:
            assert r['split']==split and r['evaluation_only']==(split=='validation')
        encoded=[encode_final(tokenizer,r)[0] for r in rows]
        saved=[json.loads(s) for s in (args.preflight_dir/f'{split}-tokenized.jsonl').read_text().splitlines()]
        assert len(encoded)==len(saved)==plan['counts'][split]
        assert all(item=={k:s[k] for k in item} for item,s in zip(encoded,saved))
        processed[split]=Dataset.from_list(encoded)
    if args.mode=='tiny-overfit':
        processed['train']=processed['train'].select(range(16))
    def collator(features):
        return {k:torch.tensor(v,dtype=torch.long) for k,v in collate_explicit(features,tokenizer.pad_token_id).items()}
    diagnostic=args.mode!='full'
    ta=TrainingArguments(output_dir=str(args.output_dir/'checkpoints'),per_device_train_batch_size=1,
        per_device_eval_batch_size=1,gradient_accumulation_steps=t['gradient_accumulation_steps'],
        num_train_epochs=t['epochs'],max_steps=plan['max_steps'],
        learning_rate=(2e-4 if args.mode=='tiny-overfit' else t['learning_rate']),warmup_steps=t['warmup_steps'],
        lr_scheduler_type=t['scheduler'],optim=t['optimizer'],weight_decay=t['weight_decay'],max_grad_norm=t['max_grad_norm'],
        bf16=True,fp16=False,seed=t['seed'],data_seed=t['seed'],logging_steps=1,
        save_strategy=plan['save_strategy'],eval_strategy=plan['eval_strategy'],save_total_limit=2,
        report_to=[] if diagnostic else ['wandb'],
        run_name=(experiment_id+'-'+args.mode if diagnostic else config.get('tracking',{}).get('run_name',
            'exp'+experiment_id.split('-')[1]+'-sft-lr'+format(t['learning_rate'],'.0e').replace('e-0','e-')+
            '-'+str(len(processed['train']))+'rows-'+format(t['epochs'],'g')+'ep')),
        remove_unused_columns=False,prediction_loss_only=True,**plan['step_kwargs'])
    class ExposureTrainer(Trainer):
        """Record only actual training microbatches, not mask checks/evaluation."""
        def training_step(self, model, inputs, *positional, **keywords):
            loss=super().training_step(model,inputs,*positional,**keywords)
            if not diagnostic:
                record=dict(optimizer_step_before=self.state.global_step,
                    supervised_tokens=int((inputs['labels']!=-100).sum().item()),
                    input_tokens=int(inputs['attention_mask'].sum().item()),
                    input_ids_sha256=hashlib.sha256(json.dumps(inputs['input_ids'].tolist()).encode()).hexdigest())
                with (args.output_dir/'training-exposure.jsonl').open('a',encoding='utf-8') as stream:
                    stream.write(json.dumps(record)+'\n')
            return loss
    trainer=ExposureTrainer(model=model,args=ta,train_dataset=processed['train'],eval_dataset=processed['validation'],data_collator=collator)
    save(args.output_dir/'effective-training-arguments.json',ta.to_dict())
    save(args.output_dir/'invocation.json',dict(argv=sys.argv,cwd=os.getcwd(),
        precision='bfloat16',float32_matmul_precision=torch.get_float32_matmul_precision(),
        allow_tf32=torch.backends.cuda.matmul.allow_tf32,
        deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
        environment={k:os.environ[k] for k in ('HF_HOME','WANDB_DIR','CUDA_VISIBLE_DEVICES','OMP_NUM_THREADS') if k in os.environ}))
    count=sum(p.numel() for p in model.parameters() if p.requires_grad)
    assert count>0
    # Verify every collated row against its saved labels, including padding.
    for split in processed:
        for i in range(0,len(processed[split]),2):
            examples=[processed[split][j] for j in range(i,min(i+2,len(processed[split])))]
            batch=collator(examples)
            for j,e in enumerate(examples):
                assert batch['labels'][j,:len(e['labels'])].tolist()==e['labels']
                assert (batch['labels'][j,len(e['labels']):]==-100).all()
    actual=next(iter(trainer.get_train_dataloader()))
    assert (actual['labels']!=-100).any()
    save(args.output_dir/'mask-check.json',dict(all_rows_verified=True,trainable_parameters=count,actual_batch_labels=actual['labels'].tolist()))
    if args.mode=='representation-check':
        save(args.output_dir/'result.json',dict(status='passed',mode=args.mode))
        return
    before=trainer.evaluate(eval_dataset=processed['train']) if args.mode=='tiny-overfit' else None
    result=trainer.train()
    assert math.isfinite(result.training_loss)
    if args.mode=='full' and plan['max_steps']>0:
        assert trainer.state.global_step==plan['max_steps']
    trainer.save_model(str(args.output_dir/'adapter'))
    tokenizer.save_pretrained(args.output_dir/'adapter')
    after=trainer.evaluate(eval_dataset=processed['train']) if args.mode=='tiny-overfit' else None
    save(args.output_dir/'result.json',dict(status='completed',mode=args.mode,metrics=result.metrics,tiny_before=before,tiny_after=after,adapter_reload_verified=False))

if __name__=='__main__':
    main()
