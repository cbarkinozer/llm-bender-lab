"""Native-label, sequential-order GPU execution for the frozen bilingual pilot."""
import argparse
import gc
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import time

from run_lfm3_sft160 import environment, dump, read, sha

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'experiments/turkish-capability/lfm3-1.7b'
PILOT = BASE/'bilingual-pilot-v01'
RUN = BASE/'bilingual-runtime-local'
EXPERIMENTS = ['exp-010-tr-only-sft160','exp-011-bilingual-sft640']


def load(experiment):
    cfg = read(BASE/experiment/'config.yaml')
    d = cfg['dataset']
    assert sha(ROOT/d['train_file']) == d['train_sha256']
    rows = [json.loads(l) for l in (ROOT/d['train_file']).read_text(encoding='utf-8').splitlines()]
    plan = read(ROOT/d['data_order_file'])
    order = plan[d['data_order_key']]
    assert len(rows) == d['train_rows']
    assert len(order) == cfg['training']['optimizer_steps']*8
    return cfg, rows, order


def native_audit(experiment):
    from transformers import AutoTokenizer
    from run_lfm3_bilingual_pilot import render
    cfg, rows, order = load(experiment)
    tokenizer = AutoTokenizer.from_pretrained(cfg['model']['parent_repo'], revision=cfg['model']['parent_revision'], trust_remote_code=True)
    template_hash = hashlib.sha256(tokenizer.chat_template.encode()).hexdigest()
    assert template_hash == 'f45005c50cd2a97329722bf3a2dee9f16c04cdf825a589b280fb7e99e6827818'
    out = RUN/'native'/experiment
    out.mkdir(parents=True,exist_ok=True)
    tokenizer.save_pretrained(out/'tokenizer')
    examples, audits = [], []
    for row in rows:
        messages = [dict(m) for m in row['messages']]
        if row['worked_solution']:
            messages[-1]['thinking'] = row['worked_solution']
        full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        prefix = tokenizer.apply_chat_template(messages[:-1], tokenize=False, add_generation_prompt=False)+'<|im_start|>assistant\n'
        assert (prefix,full) == render(row['messages'],row['worked_solution']), row['id']
        ids = tokenizer(full,add_special_tokens=False)['input_ids']
        pids = tokenizer(prefix,add_special_tokens=False)['input_ids']
        assert ids[:len(pids)] == pids
        assert 0 < len(ids) <= cfg['training']['max_length']
        labels = [-100]*len(pids)+ids[len(pids):]
        target = tokenizer.decode(ids[len(pids):],skip_special_tokens=False)
        assert target.count('<think>') == target.count('</think>') == 1
        assert row['messages'][-1]['content'] in target
        if row['worked_solution']:
            assert row['worked_solution'] in target
        else:
            assert target.startswith('<think></think>')
        assert 124900 in labels and target.rstrip().endswith('<|im_end|>')
        examples.append(dict(input_ids=ids,attention_mask=[1]*len(ids),labels=labels))
        audits.append(dict(id=row['id'],length=len(ids),masked_tokens=len(pids),supervised_tokens=len(ids)-len(pids),
                           reasoning=bool(row['worked_solution']),decoded_supervised_target=target))
    exposed = sum(audits[i]['supervised_tokens'] for i in order)
    assert exposed == cfg['training']['supervised_token_budget']
    path = out/'train-tokenized.jsonl'
    path.write_text(''.join(json.dumps(r)+'\n' for r in examples),encoding='utf-8')
    dump(out/'label-audit.json',dict(status='passed',rows=audits,train_sha256=cfg['dataset']['train_sha256'],
        tokenized_sha256=sha(path),chat_template_sha256=template_hash,supervised_exposure=exposed,
        native_template_equals_planned_renderer=True,reasoning_rows=sum(r['reasoning'] for r in audits)))
    print('NATIVE_AUDIT_PASSED '+experiment,flush=True)


def prepare():
    import run_lfm3_sft160 as parent
    # Reuse the validated pinned BF16 CPT merge and reload-parity implementation.
    # Its legacy label audit is separate; only native/<experiment> is trained here.
    parent.RUNTIME = RUN/'parent-prepare'
    parent.prepare(read(BASE/EXPERIMENTS[0]/'config.yaml'))
    for experiment in EXPERIMENTS:
        native_audit(experiment)


def fingerprints(experiment):
    cfg, rows, order = load(experiment)
    return dict(config_sha256=sha(BASE/experiment/'config.yaml'),train_sha256=cfg['dataset']['train_sha256'],
        order_sha256=sha(ROOT/cfg['dataset']['data_order_file']),runner_sha256=sha(Path(__file__)),
        tokenized_sha256=sha(RUN/'native'/experiment/'train-tokenized.jsonl'),
        parent_merge_sha256=sha(RUN/'parent-prepare/cpt-merge.json'))


def train(experiment,mode):
    import torch
    from datasets import Dataset
    from peft import LoraConfig,get_peft_model
    from torch.utils.data import SequentialSampler
    from transformers import AutoModelForCausalLM,AutoTokenizer,Trainer,TrainingArguments,TrainerCallback,set_seed
    cfg, semantic, order = load(experiment)
    t = cfg['training']
    fp = fingerprints(experiment)
    out = BASE/experiment/'results-local'/mode
    if (out/'training-manifest.json').exists():
        old = read(out/'training-manifest.json')
        assert old['status']=='passed' and old['fingerprints']==fp
        assert all(sha(out/p)==h for p,h in old['adapter_files'].items())
        print('ALREADY_COMPLETED '+experiment+' '+mode,flush=True)
        return
    assert not out.exists(), 'Incomplete output exists; preserve and inspect rather than overwrite'
    if mode=='sft':
        gate = read(RUN/'gpu-gate.json')
        assert gate['experiments'][experiment] == fp
        assert all(gate[k] for k in ['baseline_completed','native_labels_passed','smoke_passed','tiny_overfit_passed','owner_data_decisions_recorded'])
        assert read(PILOT/'plan/gates.json')['provider_terms_owner_risk_acceptance']['accepted']
    examples = [json.loads(l) for l in (RUN/'native'/experiment/'train-tokenized.jsonl').read_text().splitlines()]
    diagnostic = mode!='sft'
    if mode=='sft':
        indices = order
    elif mode=='tiny-overfit':
        # Twenty train-only examples, balanced across the four original sources.
        indices, seen = [], {}
        for i,r in enumerate(semantic):
            if r['direction']=='tr-tr' and seen.get(r['source_key'],0)<5:
                indices.append(i);seen[r['source_key']]=seen.get(r['source_key'],0)+1
        assert len(indices)==20
    else:
        indices = sorted(range(len(examples)),key=lambda i:len(examples[i]['input_ids']),reverse=True)[:8]
    selected = [examples[i] for i in indices]
    out.mkdir(parents=True)
    set_seed(t['seed'])
    model = AutoModelForCausalLM.from_pretrained(RUN/'parent-prepare/cpt-merged',dtype=torch.bfloat16,trust_remote_code=True).to('cuda')
    model.config.use_cache=False
    tokenizer = AutoTokenizer.from_pretrained(RUN/'native'/experiment/'tokenizer',trust_remote_code=True)
    model = get_peft_model(model,LoraConfig(r=t['lora_rank'],lora_alpha=t['lora_alpha'],lora_dropout=t['lora_dropout'],
        target_modules=t['target_modules'],task_type='CAUSAL_LM'))
    assert not model.get_input_embeddings().weight.requires_grad and not model.get_output_embeddings().weight.requires_grad
    model.enable_input_require_grads()
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)

    def collate(rows):
        length = max(len(r['input_ids']) for r in rows)
        batch = {k:torch.tensor([r[k]+[pad]*(length-len(r[k])) for r in rows]) for k,pad in
                 [('input_ids',tokenizer.pad_token_id),('attention_mask',0),('labels',-100)]}
        assert torch.all(batch['labels'][batch['attention_mask']==0]==-100)
        return batch

    report_to = 'wandb' if os.getenv('WANDB_API_KEY') else 'none'
    tracking = None
    if report_to=='wandb':
        import wandb
        tracking = wandb.init(project=cfg['tracking']['project'],group=cfg['tracking']['group'],
            name=cfg['tracking']['run_name'] if not diagnostic else experiment+'-'+mode,
            job_type=mode,dir=str(out),config=cfg)
        dump(out/'wandb-run.json',dict(id=tracking.id,url=tracking.url))
    steps = 3 if mode=='smoke' else 40 if mode=='tiny-overfit' else t['optimizer_steps']
    args = TrainingArguments(output_dir=str(out),num_train_epochs=1,max_steps=steps,
        per_device_train_batch_size=t['micro_batch_size'],gradient_accumulation_steps=1 if diagnostic else t['gradient_accumulation_steps'],
        learning_rate=5e-4 if mode=='tiny-overfit' else t['learning_rate'],
        lr_scheduler_type='constant' if diagnostic else t['scheduler'],warmup_steps=0 if diagnostic else t['warmup_steps'],
        bf16=True,fp16=False,optim=t['optimizer'],weight_decay=t['weight_decay'],adam_beta1=t['adam_beta1'],
        adam_beta2=t['adam_beta2'],adam_epsilon=t['adam_epsilon'],max_grad_norm=t['max_grad_norm'],
        gradient_checkpointing=t['gradient_checkpointing'],gradient_checkpointing_kwargs={'use_reentrant':False},
        seed=t['seed'],data_seed=t['data_seed'],logging_steps=1,save_strategy='steps',save_steps=10**8,
        save_only_model=False,save_total_limit=None,eval_strategy='no',report_to=report_to,
        dataloader_num_workers=0,remove_unused_columns=False,label_names=['labels'])

    class SequentialTrainer(Trainer):
        def _get_train_sampler(self,*args,**kwargs):
            return SequentialSampler(self.train_dataset)

    class Checks(TrainerCallback):
        def on_step_end(self,args,state,control,**kwargs):
            if not diagnostic and state.global_step in t['save_steps']:
                control.should_save=True
            return control

        def on_pre_optimizer_step(self,args,state,control,model=None,**kwargs):
            grads = [p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
            assert grads and all(bool(torch.isfinite(g).all()) for g in grads)
            assert any(bool(torch.count_nonzero(g)) for g in grads)

        def on_log(self,args,state,control,logs=None,**kwargs):
            for name in ['loss','grad_norm']:
                if logs and name in logs:
                    assert math.isfinite(logs[name]),(name,logs[name])

    trainer = SequentialTrainer(model=model,args=args,train_dataset=Dataset.from_list(selected),data_collator=collate,
        processing_class=tokenizer,callbacks=[Checks()])
    # Verify the actual loader begins in the planned row order and masks padding.
    first = next(iter(trainer.get_train_dataloader()))
    for i in range(min(2,len(selected))):
        assert first['input_ids'][i,:len(selected[i]['input_ids'])].tolist()==selected[i]['input_ids']
    dump(out/'first-batch.json',{k:v.tolist() for k,v in first.items()})
    sanitized = trainer.args.to_dict()
    for name in ['hub_token','push_to_hub_token']:
        sanitized.pop(name,None)
    dump(out/'effective-args.json',sanitized)
    dump(out/'data-order.json',dict(semantic_ids=[semantic[i]['id'] for i in indices],fingerprints=fp))

    def nll():
        prior = model.training;model.eval()
        total,count=0,0
        with torch.inference_mode():
            for r in selected:
                b={k:v.to('cuda') for k,v in collate([r]).items()}
                loss=model(**b).loss;n=int((b['labels'][:,1:]!=-100).sum())
                total+=float(loss)*n;count+=n
        model.train(prior)
        return total/count

    initial=nll() if mode=='tiny-overfit' else None
    started=time.monotonic()
    result=trainer.train()
    final=nll() if mode=='tiny-overfit' else None
    assert trainer.state.global_step==steps
    if mode=='tiny-overfit':
        assert final < initial*.8,(initial,final)
    if not diagnostic:
        for step in t['save_steps']:
            assert all((out/f'checkpoint-{step}'/p).exists() for p in
                       ['adapter_model.safetensors','optimizer.pt','scheduler.pt','trainer_state.json','rng_state.pth'])
    trainer.save_model(out/'adapter');tokenizer.save_pretrained(out/'adapter');trainer.save_state()
    # Verify saved adapter reload, independently of training loss.
    # Trainer's Accelerate autocast wrapper is not present on a plain reload.
    # Remove that execution wrapper so both probes use the same inference path.
    model=trainer.accelerator.unwrap_model(model,keep_fp32_wrapper=False)
    model.eval()
    probe=tokenizer('Kısa bir kayıt denemesi.',return_tensors='pt').to('cuda')
    with torch.inference_mode():
        before=model(**probe,use_cache=False).logits[:,-1].float().cpu()
    del trainer,model
    gc.collect();torch.cuda.empty_cache()
    from peft import PeftModel
    model=AutoModelForCausalLM.from_pretrained(RUN/'parent-prepare/cpt-merged',dtype=torch.bfloat16,trust_remote_code=True).to('cuda')
    model=PeftModel.from_pretrained(model,out/'adapter').eval()
    with torch.inference_mode():
        after=model(**probe,use_cache=False).logits[:,-1].float().cpu()
    dump(out/'adapter-reload-probe.json',dict(exact=torch.equal(before,after),
        max_abs_difference=float((before-after).abs().max()),
        rms_difference=float((before-after).square().mean().sqrt()),
        same_top1=bool(before.argmax()==after.argmax()),
        before_top1=int(before.argmax()),after_top1=int(after.argmax()),
        base_parameter_dtype=str(next(model.get_base_model().parameters()).dtype),
        adapter_parameter_dtypes=sorted({str(p.dtype) for n,p in model.named_parameters() if 'lora_' in n})))
    torch.save(dict(before=before,after=after,probe={k:v.cpu() for k,v in probe.items()}),out/'adapter-reload-logits.pt')
    assert torch.equal(before,after),'Saved adapter reload differs'
    generations=[]
    if mode=='smoke':
        for prompt in ['Yalnızca merhaba yaz.','2 + 3 kaçtır? Yalnızca sonucu yaz.']:
            text=tokenizer.apply_chat_template([dict(role='user',content=prompt)],tokenize=False,add_generation_prompt=True,enable_thinking=False)
            inputs=tokenizer(text,return_tensors='pt').to('cuda')
            with torch.inference_mode():
                output=model.generate(**inputs,max_new_tokens=48,do_sample=False,repetition_penalty=1.1,eos_token_id=124900,pad_token_id=tokenizer.pad_token_id)
            generated=output[0,inputs['input_ids'].shape[1]:].tolist()
            prediction=tokenizer.decode(generated,skip_special_tokens=False)
            assert prediction.strip() and all(isinstance(v,int) for v in generated)
            generations.append(dict(prompt=prompt,prediction=prediction,token_ids=generated))
    manifest=dict(status='passed',experiment=experiment,mode=mode,fingerprints=fp,optimizer_steps=steps,
        initial_train_nll=initial,final_train_nll=final,training=result.metrics,wall_seconds=time.monotonic()-started,
        trainable_parameters=trainable,adapter_reload_exact=True,smoke_generations=generations,
        packages={p:importlib.metadata.version(p) for p in ['torch','transformers','peft','datasets','accelerate','wandb']},
        gpu=torch.cuda.get_device_name(),wandb_url=tracking.url if tracking else None,
        max_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
        adapter_files={p.relative_to(out).as_posix():sha(p) for p in (out/'adapter').iterdir() if p.is_file()})
    dump(out/'training-manifest.json',manifest)
    if tracking:
        tracking.finish()
    print(json.dumps({k:manifest[k] for k in ['status','experiment','mode','optimizer_steps','wall_seconds','initial_train_nll','final_train_nll']}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',required=True,choices=['prepare','native-audit','smoke','tiny-overfit','sft'])
    parser.add_argument('--experiment',default=EXPERIMENTS[0],choices=EXPERIMENTS)
    args=parser.parse_args();environment()
    if args.mode=='prepare':prepare()
    elif args.mode=='native-audit':native_audit(args.experiment)
    else:train(args.experiment,args.mode)
