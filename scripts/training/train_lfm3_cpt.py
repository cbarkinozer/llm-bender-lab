"""Notebook-derived CPT recipe on the separately frozen Wikipedia train split.

Run baseline and GPU smoke before training. Raw text supervision, not chat SFT.
"""
import argparse
import hashlib
import json
import random
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--tiny-overfit', action='store_true')
    parser.add_argument('--wandb-project', default='lfm3-turkish-post-training')
    args = parser.parse_args()
    if args.smoke and args.tiny_overfit:
        parser.error('Choose one diagnostic mode')
    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTConfig, SFTTrainer
    base = args.experiment_dir
    config = json.loads((base / 'config-planned.json').read_text())
    manifest_file = base / config['active_cpt_manifest']
    data_root = base / config['active_cpt_data']
    data_manifest = json.loads(manifest_file.read_text())
    model_cfg = config['model']
    # Reject absent/stale authorization evidence before loading weights or W&B.
    if not args.smoke and not args.tiny_overfit:
        gate_file = base / 'data-local/gpu-gate.json'
        gate = json.loads(gate_file.read_text()) if gate_file.exists() else {}
        if not all(gate.get(k) for k in ('baseline_completed','training_smoke_passed','labels_audited','tiny_overfit_passed')):
            raise ValueError('Full CPT requires recorded baseline, smoke, label and tiny-overfit gates')
        if gate.get('model_revision') != model_cfg['revision'] or gate.get('data_manifest_sha256') != hashlib.sha256(manifest_file.read_bytes()).hexdigest():
            raise ValueError('GPU gate refers to another model/data revision')
    def load(name):
        file = data_root / (name + '.jsonl')
        if hashlib.sha256(file.read_bytes()).hexdigest() != data_manifest['splits'][name]['sha256']:
            raise ValueError('Frozen CPT input hash mismatch')
        rows = [json.loads(line) for line in file.read_text(encoding='utf-8').splitlines()]
        return Dataset.from_list([dict(text=r['text']) for r in rows])
    train, dev = load(config.get('cpt_train_split','wiki_train')), load('wiki_dev')
    if args.smoke:
        train, dev = train.select(range(8)), dev.select(range(4))
    if args.tiny_overfit:
        train = train.select(range(2))
        dev = train
    args.output_dir.mkdir(parents=True, exist_ok=False)
    tokenizer = AutoTokenizer.from_pretrained(model_cfg['repo'], revision=model_cfg['revision'])
    model = AutoModelForCausalLM.from_pretrained(model_cfg['repo'], revision=model_cfg['revision'],
        code_revision=model_cfg['revision'], trust_remote_code=True, dtype=torch.bfloat16)
    lora = LoraConfig(r=64, lora_alpha=64, lora_dropout=0.,
        target_modules=['q_proj','k_proj','v_proj','o_proj','in_proj','out_proj','w1','w2','w3'],
        task_type='CAUSAL_LM')
    settings = dict(num_train_epochs=1, per_device_train_batch_size=2, gradient_accumulation_steps=4,
        learning_rate=2e-4, lr_scheduler_type='cosine', warmup_steps=0.05, max_length=2048,
        packing=True, packing_strategy='wrapped', dataset_text_field='text', completion_only_loss=False,
        logging_steps=1 if args.smoke else 10, eval_strategy='no', save_strategy='no',
        bf16=True, fp16=False, report_to='wandb', seed=3407, data_seed=3407,
        optim='adamw_torch_fused',weight_decay=0.,adam_beta1=.9,adam_beta2=.999,
        adam_epsilon=1e-8,max_grad_norm=1.,gradient_checkpointing=True,dataloader_num_workers=0)
    if 'training' in config:
        expected=config['training']
        mapping=dict(epochs='num_train_epochs',micro_batch_size='per_device_train_batch_size',
            gradient_accumulation_steps='gradient_accumulation_steps',learning_rate='learning_rate',
            scheduler='lr_scheduler_type',warmup_fraction='warmup_steps',max_length='max_length',
            packing='packing',packing_strategy='packing_strategy',seed='seed',optimizer='optim',
            weight_decay='weight_decay',adam_beta1='adam_beta1',adam_beta2='adam_beta2',
            adam_epsilon='adam_epsilon',max_grad_norm='max_grad_norm',
            gradient_checkpointing='gradient_checkpointing',dataloader_num_workers='dataloader_num_workers')
        for field,key in mapping.items():
            if expected[field]!=settings[key]: raise ValueError('Config/runner disagreement: '+field)
        if (expected['lora_rank'],expected['lora_alpha'],expected['lora_dropout'],expected['embeddings_trainable']) != (lora.r,lora.lora_alpha,lora.lora_dropout,False):
            raise ValueError('Config/runner LoRA disagreement')
        if set(expected['target_modules'])!=set(lora.target_modules):
            raise ValueError('Config/runner target modules disagreement')
    if args.smoke:
        settings['max_steps'] = 2
    if args.tiny_overfit:
        settings.update(max_steps=30,logging_steps=1,gradient_accumulation_steps=1)
    import wandb
    mode = 'smoke' if args.smoke else 'tiny-overfit' if args.tiny_overfit else 'train'
    run_label=config.get('cpt_run_label','lfm3-1.7b-cpt-wikipedia-2m2-lora-r64-lr2e-4-seed3407')
    tracking = wandb.init(project=args.wandb_project,
        name=f'{run_label}-{mode}',
        group=config.get('tracking',{}).get('group','lfm3-1.7b-turkish-wikipedia-cpt-v01'), job_type='cpt-'+mode,
        config=dict(model=model_cfg, settings=settings,
            data_manifest_sha256=hashlib.sha256(manifest_file.read_bytes()).hexdigest()),
        dir=str(args.output_dir))
    (args.output_dir/'wandb-run.json').write_text(json.dumps(dict(id=tracking.id,url=tracking.url))+'\n')
    class ExposureTrainer(SFTTrainer):
        def training_step(self, model, inputs, *positional, **kwargs):
            with (args.output_dir/'token-exposure.jsonl').open('a') as stream:
                stream.write(json.dumps(dict(step=self.state.global_step,
                    input_tokens=int(inputs['input_ids'].numel()),
                    supervised_tokens=int((inputs['labels']!=-100).sum())))+'\n')
            return super().training_step(model, inputs, *positional, **kwargs)
    trainer = ExposureTrainer(model=model, args=SFTConfig(output_dir=str(args.output_dir), **settings),
        train_dataset=train, eval_dataset=dev, processing_class=tokenizer, peft_config=lora)
    trainer.model.print_trainable_parameters()
    if trainer.model.get_input_embeddings().weight.requires_grad or trainer.model.get_output_embeddings().weight.requires_grad:
        raise ValueError('Notebook-derived CPT recipe requires frozen embeddings/head')
    if not any(p.requires_grad for p in trainer.model.parameters()):
        raise ValueError('No trainable LoRA parameters')
    effective_args=trainer.args.to_dict()
    for secret_field in ('hub_token','push_to_hub_token','wandb_api_key'):
        effective_args.pop(secret_field,None)
    (args.output_dir/'effective-training-args.json').write_text(json.dumps(effective_args,indent=2,default=str)+'\n')
    (args.output_dir/'training-representation.json').write_text(json.dumps(dict(
        raw_train_documents=len(train),raw_dev_documents=len(dev),
        packed_train_rows=len(trainer.train_dataset),packed_dev_rows=len(trainer.eval_dataset),
        trainable_parameters=sum(p.numel() for p in trainer.model.parameters() if p.requires_grad),
        total_parameters=sum(p.numel() for p in trainer.model.parameters()),eos_token_id=tokenizer.eos_token_id),indent=2)+'\n')
    batch = next(iter(trainer.get_train_dataloader()))
    active = batch.get('attention_mask', torch.ones_like(batch['labels'])).bool()
    if not torch.equal(batch['labels'][active], batch['input_ids'][active]) or not torch.all(batch['labels'][~active] == -100):
        raise ValueError('Actual model CPT all-token label audit failed')
    (args.output_dir/'label-audit.json').write_text(json.dumps(dict(status='passed',
        supervised_tokens=int((batch['labels']!=-100).sum()), padding_tokens=int((~active).sum())))+'\n')
    (args.output_dir/'representation-first-batch.json').write_text(json.dumps(
        {key:value.tolist() for key,value in batch.items() if isinstance(value,torch.Tensor)})+'\n')
    initial_evaluation = trainer.evaluate() if args.tiny_overfit else None
    result = trainer.train()
    evaluation = trainer.evaluate()
    trainer.save_model(str(args.output_dir / 'adapter'))
    tokenizer.save_pretrained(args.output_dir / 'adapter')
    trainer.save_state()
    torch.save(dict(optimizer=trainer.optimizer.state_dict(), scheduler=trainer.lr_scheduler.state_dict(),
        python_rng=random.getstate(),torch_rng=torch.get_rng_state(), cuda_rng=torch.cuda.get_rng_state_all()),
        args.output_dir/'optimizer-scheduler-rng.pt')
    report = dict(status='tiny_overfit_completed_requires_loss_review' if args.tiny_overfit else 'smoke_completed' if args.smoke else 'training_completed', model=model_cfg,
        initial_evaluation=initial_evaluation,
        training=result.metrics, development=evaluation, settings=settings,
        peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
        attention_implementation=getattr(trainer.model.config,'_attn_implementation',None),
        source_manifest_sha256=hashlib.sha256(manifest_file.read_bytes()).hexdigest(),
        deviations_from_notebook=['Pinned model and data; screened disjoint document splits',
            'Fixed seed', 'End-of-run dev evaluation rather than every 100 steps',
            'Explicit all-token loss', 'W&B tracking enabled for GPU runs'])
    (args.output_dir / 'training-manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if not args.smoke and not args.tiny_overfit:
        artifact = wandb.Artifact(run_label+'-adapter',type='model',
            metadata=dict(model=model_cfg,settings=settings))
        artifact.add_dir(str(args.output_dir/'adapter'),name='adapter')
        for name in ('training-manifest.json','label-audit.json','token-exposure.jsonl','trainer_state.json'):
            artifact.add_file(str(args.output_dir/name),name=name)
        tracking.log_artifact(artifact).wait()
    tracking.finish()


if __name__ == '__main__':
    main()
