"""Explicit native-template labels for the owner-reviewed LFM3 pilot160 pair."""
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
DATA = BASE / 'sft-pilot160-v01'
RUNTIME = BASE / 'pilot160-runtime-local'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def environment():
    os.environ.setdefault('HF_HOME', '/workspace/.cache/huggingface')
    os.environ.setdefault('WANDB_DIR', '/workspace/.cache/wandb')
    private = Path('/workspace/private-credentials.json')
    if private.exists():
        for k, v in read(private).items():
            os.environ[k] = v.strip()
    # Detached children must establish their own W&B service.
    for k in list(os.environ):
        if k.startswith('WANDB_SERVICE'):
            del os.environ[k]


def prepare(cfg, audit_only=False, tokenizer_path=None):
    from transformers import AutoTokenizer
    model_cfg = cfg['model']
    RUNTIME.mkdir(parents=True, exist_ok=True)
    if tokenizer_path:
        assert audit_only, 'Local tokenizer override is audit-only'
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True, trust_remote_code=True)
    else:
        tokenizer = AutoTokenizer.from_pretrained(model_cfg['parent_repo'], revision=model_cfg['parent_revision'],
                                                 trust_remote_code=True)
    assert hashlib.sha256(tokenizer.chat_template.encode()).hexdigest() == 'f45005c50cd2a97329722bf3a2dee9f16c04cdf825a589b280fb7e99e6827818'
    tokenizer.save_pretrained(RUNTIME / 'tokenizer')
    dm = read(DATA / 'manifest.json')
    for name, digest in dm['files'].items():
        assert sha(DATA / name) == digest, name
    examples, audits = [], []
    for line in (DATA / 'train.jsonl').read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        assert row['split'] == 'train'
        ms = [dict(m) for m in row['messages']]
        assert ms[-1]['role'] == 'assistant'
        if row['worked_solution']:
            ms[-1]['thinking'] = row['worked_solution']
        rendered = tokenizer.apply_chat_template(ms, tokenize=False, add_generation_prompt=False)
        prefix = tokenizer.apply_chat_template(ms[:-1], tokenize=False, add_generation_prompt=False)
        prefix += '<|im_start|>assistant\n'
        assert rendered.startswith(prefix)
        ids = tokenizer(rendered, add_special_tokens=False)['input_ids']
        prefix_ids = tokenizer(prefix, add_special_tokens=False)['input_ids']
        assert ids[:len(prefix_ids)] == prefix_ids, 'Token boundary changed'
        labels = [-100] * len(prefix_ids) + ids[len(prefix_ids):]
        assert 0 < len(ids) <= cfg['training']['max_length']
        target = tokenizer.decode(ids[len(prefix_ids):], skip_special_tokens=False)
        assert target.count('<think>') == target.count('</think>') == 1
        assert row['messages'][-1]['content'] in target
        if row['worked_solution']:
            assert row['worked_solution'] in target
        else:
            assert target.startswith('<think></think>')
        assert 124900 in labels and target.rstrip().endswith('<|im_end|>')
        end = max(i for i, token in enumerate(ids) if token == 124900)
        assert labels[end] == 124900 and not tokenizer.decode(ids[end+1:]).strip()
        assert tokenizer.decode([124900]) == '<|im_end|>'
        examples.append(dict(input_ids=ids, attention_mask=[1]*len(ids), labels=labels))
        audits.append(dict(id=row['id'], length=len(ids), masked_tokens=len(prefix_ids),
                           supervised_tokens=len(ids)-len(prefix_ids), reasoning=bool(row['worked_solution']),
                           decoded_supervised_target=target, rendered_text=rendered))
    assert len(examples) == 160
    (RUNTIME / 'train-tokenized.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in examples))
    dump(RUNTIME / 'label-audit.json', dict(status='passed', rows=audits,
         min_length=min(r['length'] for r in audits), max_length=max(r['length'] for r in audits),
         tokenized_sha256=sha(RUNTIME / 'train-tokenized.jsonl'), semantic_manifest_sha256=sha(DATA / 'manifest.json'),
         chat_template_sha256=hashlib.sha256(tokenizer.chat_template.encode()).hexdigest()))
    if audit_only:
        return
    import torch
    from transformers import AutoModelForCausalLM
    from peft import PeftModel
    from huggingface_hub import snapshot_download
    destination = RUNTIME / 'cpt-merged'
    if destination.exists() and (RUNTIME / 'cpt-merge.json').exists():
        receipt = read(RUNTIME / 'cpt-merge.json')
        assert receipt['pinned_model'] == model_cfg
        assert all(sha(destination/name)==digest for name,digest in receipt['files'].items())
        return
    adapter = snapshot_download(model_cfg['repo'], revision=model_cfg['revision'])
    assert (Path(adapter) / 'adapter_config.json').exists(), 'Expected published adapter'
    model = AutoModelForCausalLM.from_pretrained(model_cfg['parent_repo'], revision=model_cfg['parent_revision'],
        code_revision=model_cfg['parent_revision'], trust_remote_code=True, dtype=torch.bfloat16).to('cuda')
    model = PeftModel.from_pretrained(model, adapter).eval()
    probe = tokenizer('Bu bir kayıt ve yeniden yükleme denemesidir.', return_tensors='pt').to('cuda')
    with torch.inference_mode():
        before = model(**probe, use_cache=False).logits[:, -1].float().cpu()
    model = model.merge_and_unload(safe_merge=True).eval()
    with torch.inference_mode():
        merged = model(**probe, use_cache=False).logits[:, -1].float().cpu()
    assert torch.isfinite(merged).all()
    model.save_pretrained(destination, safe_serialization=True)
    tokenizer.save_pretrained(destination)
    del model
    torch.cuda.empty_cache()
    model = AutoModelForCausalLM.from_pretrained(destination, dtype=torch.bfloat16,
                                               trust_remote_code=True).to('cuda').eval()
    with torch.inference_mode():
        reloaded = model(**probe, use_cache=False).logits[:, -1].float().cpu()
    assert torch.equal(merged, reloaded), 'Reload changed merged weights/logits'
    dump(RUNTIME / 'cpt-merge.json', dict(status='passed', pinned_model=model_cfg,
         merged_reload_exact=True, before_after_top1_agrees=bool(before.argmax()==merged.argmax()),
         max_abs_merge_difference=float((before-merged).abs().max()),
         bf16_rounding_note='BF16 merge is the common initialization and inference baseline for both runs',
         files={p.name:sha(p) for p in destination.iterdir() if p.is_file()}))
    print('Native labels, CPT merge and reload passed', flush=True)


def train(cfg, mode, resume_checkpoint=None):
    import torch
    import wandb
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, TrainerCallback, set_seed
    t = cfg['training']
    experiment = BASE / cfg['experiment']['id']
    out = experiment / 'results-local' / mode
    if mode == 'sft':
        gate = read(RUNTIME / 'gpu-gate.json')
        assert all(gate.get(k) for k in ['baseline_completed','labels_audited','smoke_passed','tiny_overfit_passed','semantic_review_passed'])
        assert gate['semantic_manifest_sha256'] == sha(DATA / 'manifest.json')
        assert gate['tokenized_sha256'] == sha(RUNTIME / 'train-tokenized.jsonl')
        assert gate['model_revision'] == cfg['model']['revision']
        assert gate['training_source_sha256'] == sha(Path(__file__))
        assert gate['config_sha256'][cfg['experiment']['id']] == sha(experiment/'config.yaml')
        assert gate['dev_packet_sha256'] == sha(BASE/'sft160-dev-v01/questions.jsonl')
    if resume_checkpoint:
        assert mode == 'sft', 'Resume only a production SFT checkpoint'
        assert resume_checkpoint.resolve() in [(out/f'checkpoint-{n}').resolve() for n in t['save_steps']]
        assert all((resume_checkpoint/n).exists() for n in ['adapter_model.safetensors','optimizer.pt','scheduler.pt','rng_state.pth','trainer_state.json'])
    out.mkdir(parents=True, exist_ok=bool(resume_checkpoint))
    examples = [json.loads(s) for s in (RUNTIME / 'train-tokenized.jsonl').read_text().splitlines()]
    if mode == 'smoke':
        examples = examples[:4] + examples[80:84]
    if mode == 'tiny-overfit':
        # Twenty train-only examples, five/source (frozen reviewed file interleaves sources).
        semantic = [json.loads(s) for s in (DATA / 'train.jsonl').read_text(encoding='utf-8').splitlines()]
        seen = {}
        chosen = []
        for i in range(80,160):
            r = semantic[i]
            source = r['source_key']
            if seen.get(source, 0) < 5:
                chosen.append(examples[i]); seen[source] = seen.get(source, 0) + 1
        examples = chosen
        assert len(examples) == 20
    set_seed(t['seed'])
    model = AutoModelForCausalLM.from_pretrained(RUNTIME/'cpt-merged', dtype=torch.bfloat16,
                                               trust_remote_code=True).to('cuda')
    model.config.use_cache = False
    tokenizer = AutoTokenizer.from_pretrained(RUNTIME/'tokenizer', trust_remote_code=True)
    model = get_peft_model(model, LoraConfig(r=t['lora_rank'], lora_alpha=t['lora_alpha'],
        lora_dropout=t['lora_dropout'], target_modules=t['target_modules'], task_type='CAUSAL_LM'))
    assert not model.get_input_embeddings().weight.requires_grad
    assert not model.get_output_embeddings().weight.requires_grad
    model.enable_input_require_grads()
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    assert 0 < trainable < total / 5

    def collate(rows):
        length = max(len(r['input_ids']) for r in rows)
        batch = {}
        for k, pad in [('input_ids',tokenizer.pad_token_id),('attention_mask',0),('labels',-100)]:
            batch[k] = torch.tensor([r[k]+[pad]*(length-len(r[k])) for r in rows])
        assert torch.all(batch['labels'][batch['attention_mask']==0] == -100)
        assert torch.all((batch['labels']!=-100).sum(1)>0)
        return batch

    diagnostic = mode != 'sft'
    args = TrainingArguments(output_dir=str(out), num_train_epochs=t['epochs'],
        max_steps=3 if mode=='smoke' else 40 if mode=='tiny-overfit' else -1,
        per_device_train_batch_size=t['micro_batch_size'],
        gradient_accumulation_steps=1 if diagnostic else t['gradient_accumulation_steps'],
        learning_rate=5e-4 if mode=='tiny-overfit' else t['learning_rate'],
        lr_scheduler_type='constant' if diagnostic else t['scheduler'], warmup_steps=0 if diagnostic else t['warmup_steps'],
        bf16=True, fp16=False, optim=t['optimizer'], weight_decay=t['weight_decay'],
        adam_beta1=t['adam_beta1'], adam_beta2=t['adam_beta2'], adam_epsilon=t['adam_epsilon'],
        max_grad_norm=t['max_grad_norm'], gradient_checkpointing=t['gradient_checkpointing'],
        gradient_checkpointing_kwargs={'use_reentrant':False}, seed=t['seed'], data_seed=t['data_seed'],
        logging_steps=1, save_strategy='no' if diagnostic else 'steps', save_steps=60,
        save_only_model=False, save_total_limit=None, eval_strategy='no', report_to='wandb',
        dataloader_num_workers=0, remove_unused_columns=False, label_names=['labels'])
    tracking = wandb.init(project=cfg['tracking']['project'], group=cfg['tracking']['group'],
        name=cfg['tracking']['run_name'] if not diagnostic else 'pilot160-'+mode,
        job_type=mode, dir=str(out), config=cfg)
    dump(out/'wandb-run.json', dict(id=tracking.id,url=tracking.url))
    class Audit(TrainerCallback):
        def on_step_end(self, args, state, control, **kwargs):
            if not diagnostic and state.global_step in t['save_steps']:
                control.should_save = True
            return control
        def on_pre_optimizer_step(self, args, state, control, model=None, **kwargs):
            gradients = [p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
            assert gradients and all(bool(torch.isfinite(g).all()) for g in gradients)
            assert any(bool(torch.count_nonzero(g)) for g in gradients)
        def on_log(self, args, state, control, logs=None, **kwargs):
            if logs:
                for name in ['loss','grad_norm']:
                    if name in logs:
                        assert math.isfinite(logs[name]), (name, logs[name])
    trainer = Trainer(model=model, args=args, train_dataset=Dataset.from_list(examples),
                      data_collator=collate, processing_class=tokenizer, callbacks=[Audit()])
    first = next(iter(trainer.get_train_dataloader()))
    dump(out/'first-batch.json', {k:v.tolist() for k,v in first.items()})
    sanitized = trainer.args.to_dict()
    for k in ['hub_token','push_to_hub_token']:
        sanitized.pop(k, None)
    dump(out/'effective-args.json', sanitized)
    # Evaluate only the tiny diagnostic's own training samples; no test data.
    def train_nll():
        was_training = model.training; model.eval()
        loss_sum = count = 0
        with torch.inference_mode():
            for r in examples:
                batch = {k:v.to('cuda') for k,v in collate([r]).items()}
                loss = model(**batch).loss
                n = int((batch['labels'][:,1:]!=-100).sum())
                loss_sum += float(loss)*n; count += n
        model.train(was_training)
        return loss_sum/count
    initial = train_nll() if mode=='tiny-overfit' else None
    start = time.monotonic()
    result = trainer.train(resume_from_checkpoint=str(resume_checkpoint) if resume_checkpoint else None)
    final = train_nll() if mode=='tiny-overfit' else None
    if mode=='tiny-overfit':
        assert final < initial*.8, (initial, final)
    if mode=='sft':
        assert trainer.state.global_step == 100
        for step in t['save_steps']:
            checkpoint = out / f'checkpoint-{step}'
            assert all((checkpoint/name).exists() for name in ['adapter_model.safetensors','optimizer.pt','scheduler.pt','trainer_state.json','rng_state.pth']), checkpoint
    trainer.save_model(out/'adapter'); tokenizer.save_pretrained(out/'adapter'); trainer.save_state()
    model.eval()
    probe = {k:v.to('cuda') for k,v in collate([examples[0]]).items() if k!='labels'}
    with torch.inference_mode():
        before = model(**probe).logits[:,-1].float().cpu()
    # Merge, save, and reload: inference always uses a complete BF16 checkpoint.
    merged = model.merge_and_unload(safe_merge=True).eval()
    merged.config.use_cache = True
    with torch.inference_mode():
        after = merged(**probe, use_cache=False).logits[:,-1].float().cpu()
    merged.save_pretrained(out/'merged-model',safe_serialization=True)
    tokenizer.save_pretrained(out/'merged-model')
    del trainer, model, merged
    import gc
    gc.collect(); torch.cuda.empty_cache()
    reloaded = AutoModelForCausalLM.from_pretrained(out/'merged-model',dtype=torch.bfloat16,
                                                 trust_remote_code=True).to('cuda').eval()
    with torch.inference_mode():
        reload_logits = reloaded(**probe, use_cache=False).logits[:,-1].float().cpu()
    assert torch.equal(after,reload_logits)
    report = dict(status='passed',mode=mode,configuration=cfg,optimizer_steps=result.global_step,
        training=result.metrics,initial_train_nll=initial,final_train_nll=final,
        merge_reload_exact=True,max_abs_merge_difference=float((before-after).abs().max()),
        trainable_parameters=trainable,total_parameters=total,wall_seconds=time.monotonic()-start,
        max_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
        packages={k:importlib.metadata.version(k) for k in ['torch','transformers','trl','peft','datasets','wandb']},
        gpu=torch.cuda.get_device_name(),tokenized_sha256=sha(RUNTIME/'train-tokenized.jsonl'),
        semantic_manifest_sha256=sha(DATA/'manifest.json'),
        implementation='Transformers Trainer + explicit pretokenized native assistant labels; no automatic TRL preprocessing',
        source_sha256=sha(Path(__file__)),wandb_url=tracking.url,
        model_files={p.name:sha(p) for p in (out/'merged-model').iterdir() if p.is_file()})
    dump(out/'training-manifest.json',report)
    tracking.finish()
    print(json.dumps({k:report[k] for k in ['status','mode','optimizer_steps','wall_seconds','initial_train_nll','final_train_nll']}), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--experiment', default='exp-007-sft160-lr1e4')
    p.add_argument('--mode', choices=['audit','prepare','smoke','tiny-overfit','sft'], required=True)
    p.add_argument('--tokenizer-path', type=Path, help='Audit-only offline tokenizer path; native template fingerprint must match')
    p.add_argument('--resume-checkpoint', type=Path, help='Explicit resume from this experiment checkpoint60/100 after inspecting a failed run')
    a = p.parse_args(); environment()
    cfg = read(BASE/a.experiment/'config.yaml')
    if a.mode in ['audit','prepare']:
        prepare(cfg, audit_only=a.mode=='audit', tokenizer_path=a.tokenizer_path)
    else:
        train(cfg,a.mode,resume_checkpoint=a.resume_checkpoint)


if __name__=='__main__':
    main()
