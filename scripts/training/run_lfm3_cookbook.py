"""Native TRL completion-mask audit and isolated cookbook SFT experiments."""
import argparse, gc, hashlib, importlib.metadata, json, math, os, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/turkish-capability/lfm3-1.7b'
RUN=BASE/'cookbook-runtime-local'
EXPS=['exp-014-completion-mask','exp-015-cookbook-recipe']
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]

def train(exp,mode):
    import torch
    from datasets import Dataset
    from peft import LoraConfig, PeftModel, get_peft_model
    from torch.utils.data import SequentialSampler
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainerCallback, set_seed
    from trl import SFTConfig,SFTTrainer
    cfg=read(BASE/exp/'config.json');source=ROOT/cfg['dataset_file']
    assert sha(source)==cfg['dataset_sha256']
    audit=read(BASE/'cookbook-sft-v01/audit.json');data=rows(source)
    out=BASE/exp/'results-local'/mode
    assert not out.exists(),'Preserve existing attempt before retrying'
    out.mkdir(parents=True)
    set_seed(cfg['seed'])
    tok=AutoTokenizer.from_pretrained(cfg['model']['repo'],revision=cfg['model']['revision'],padding_side='left')
    assert hashlib.sha256(tok.chat_template.encode()).hexdigest()=='f45005c50cd2a97329722bf3a2dee9f16c04cdf825a589b280fb7e99e6827818'
    model=AutoModelForCausalLM.from_pretrained(cfg['model']['repo'],revision=cfg['model']['revision'],code_revision=cfg['model']['revision'],trust_remote_code=True,dtype=torch.bfloat16).to('cuda')
    model.config.use_cache=False
    model=get_peft_model(model,LoraConfig(r=cfg['r'],lora_alpha=cfg['lora_alpha'],lora_dropout=cfg['lora_dropout'],target_modules=cfg['target_modules'],task_type='CAUSAL_LM'))
    model.enable_input_require_grads()
    assert not model.get_input_embeddings().weight.requires_grad and not model.get_output_embeddings().weight.requires_grad
    class Ordered(SFTTrainer):
        def _get_train_sampler(self,*args,**kwargs):return SequentialSampler(self.train_dataset)
    diagnostic=mode!='sft'
    old=read(BASE/'exp-012-base-bilingual/config.yaml')['training']
    args=dict(output_dir=str(out),per_device_train_batch_size=cfg['per_device_train_batch_size'],
              gradient_accumulation_steps=1 if diagnostic else cfg['gradient_accumulation_steps'],
              learning_rate=5e-4 if mode=='tiny-overfit' else cfg['learning_rate'],
              max_length=4096,completion_only_loss=True,assistant_only_loss=False,packing=False,
              bf16=True,fp16=False,gradient_checkpointing=True,gradient_checkpointing_kwargs={'use_reentrant':False},
              seed=3407,data_seed=3407,logging_steps=1,save_strategy='no',eval_strategy='no',report_to='none',
              dataloader_num_workers=0,optim=old['optimizer'],weight_decay=old['weight_decay'],
              adam_beta1=old['adam_beta1'],adam_beta2=old['adam_beta2'],adam_epsilon=old['adam_epsilon'],max_grad_norm=old['max_grad_norm'])
    if diagnostic:args.update(max_steps=40 if mode=='tiny-overfit' else 3,warmup_steps=0,lr_scheduler_type='constant')
    elif exp==EXPS[0]:args.update(max_steps=113,warmup_steps=6,lr_scheduler_type='cosine')
    else:args.update(num_train_epochs=1,warmup_steps=.05,lr_scheduler_type='cosine')
    checks=[]
    class Check(TrainerCallback):
        def on_step_end(self,args,state,control,**kwargs):
            if not diagnostic and exp==EXPS[0] and state.global_step==69:control.should_training_stop=True
            return control
        def on_pre_optimizer_step(self,args,state,control,model=None,**kwargs):
            gradients=[p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
            assert gradients and all(bool(torch.isfinite(g).all()) for g in gradients)
            assert any(bool(torch.count_nonzero(g)) for g in gradients)
            checks.append(state.global_step)
        def on_log(self,args,state,control,logs=None,**kwargs):
            for k in ['loss','grad_norm']:
                if logs and k in logs:assert math.isfinite(logs[k])
    trainer=Ordered(model=model,args=SFTConfig(**args),train_dataset=Dataset.from_list(data),processing_class=tok,callbacks=[Check()])
    prepared=trainer.train_dataset
    assert len(prepared)==640
    audited=[]
    for i,expected in enumerate(audit['examples']):
        r=prepared[i]
        batch=trainer.data_collator([r])
        ids=batch['input_ids'][0].tolist();labels=batch['labels'][0].tolist()
        mask=batch['attention_mask'][0].tolist()
        target=tok.decode([v for v in labels if v!=-100],skip_special_tokens=False)
        assert target==expected['decoded_target'],(i,target[:100],expected['decoded_target'][:100])
        assert sum(v!=-100 for v in labels)==expected['new_supervised_tokens']
        assert sum(mask)==expected['length'] and len(ids)<=4096
        first=next(j for j,v in enumerate(labels) if v!=-100)
        assert all(v==-100 for v in labels[:first]) and labels[first:]==ids[first:]
        assert 124900 in labels
        if not expected['reasoning']:assert '<think>' not in target and '</think>' not in target
        audited.append(dict(id=expected['id'],reasoning=expected['reasoning'],supervised_tokens=len(labels)-first,decoded_target=target))
    # Padding audit uses unequal sequence lengths and checks the actual collator.
    mixed=trainer.data_collator([prepared[0],prepared[max(range(640),key=lambda i:len(prepared[i]['input_ids']))]])
    assert torch.all(mixed['labels'][mixed['attention_mask']==0]==-100)
    dump(out/'native-trl-mask-audit.json',dict(status='passed',rows=audited,supervised_tokens=sum(r['supervised_tokens'] for r in audited),padding_mask_passed=True))
    if mode=='audit':print('ALL_640_NATIVE_TRL_MASKS_PASSED',flush=True);return
    if mode=='sft':
        for prior in ['smoke','tiny-overfit']:
            manifest=read(BASE/exp/'results-local'/prior/'training-manifest.json')
            assert manifest['status']=='passed' and manifest['dataset_sha256']==sha(source)
    if mode=='tiny-overfit':indices=list(range(0,80,4))
    elif mode=='smoke':indices=sorted(range(640),key=lambda i:len(prepared[i]['input_ids']),reverse=True)[:8]
    elif exp==EXPS[0]:indices=read(BASE/'bilingual-pilot-v01/revisions/v01-corrections-02/token-budget-and-order.json')['order_b']
    else:indices=list(range(640))
    trainer.train_dataset=prepared.select(indices)
    first=next(iter(trainer.get_train_dataloader()))
    for j in range(min(cfg['per_device_train_batch_size'],len(indices))):
        actual=first['input_ids'][j][first['attention_mask'][j].bool()].tolist()
        assert actual==prepared[indices[j]]['input_ids']
    dump(out/'first-batch.json',{k:v.tolist() for k,v in first.items()})
    dump(out/'data-order.json',dict(indices=indices,expected_consumed_rows=552 if exp==EXPS[0] and mode=='sft' else None))
    effective=trainer.args.to_dict()
    for k in ['hub_token','push_to_hub_token']:effective.pop(k,None)
    dump(out/'effective-args.json',effective)
    def nll():
        model.eval();total=count=0
        with torch.inference_mode():
            for r in trainer.train_dataset:
                b={k:v.to('cuda') for k,v in trainer.data_collator([r]).items()}
                n=int((b['labels'][:,1:]!=-100).sum());total+=float(model(**b).loss)*n;count+=n
        model.train();return total/count
    initial=nll() if mode=='tiny-overfit' else None
    start=time.monotonic();result=trainer.train();final=nll() if mode=='tiny-overfit' else None
    expected=40 if mode=='tiny-overfit' else 3 if mode=='smoke' else 69 if exp==EXPS[0] else 40
    assert trainer.state.global_step==expected and len(checks)==expected
    if mode=='tiny-overfit':assert final<initial*.8,(initial,final)
    trainer.save_model(out/'adapter');tok.save_pretrained(out/'adapter');trainer.save_state()
    # Optimizer/scheduler/RNG stay on pod and in backup, without base weights.
    trainer._save_optimizer_and_scheduler(str(out));trainer._save_rng_state(str(out))
    model=trainer.accelerator.unwrap_model(model,keep_fp32_wrapper=False).eval()
    probe=tok('A short save and reload test.',return_tensors='pt').to('cuda')
    with torch.inference_mode():before=model(**probe,use_cache=False).logits[:,-1].float().cpu()
    del trainer,model;gc.collect();torch.cuda.empty_cache()
    model=AutoModelForCausalLM.from_pretrained(cfg['model']['repo'],revision=cfg['model']['revision'],code_revision=cfg['model']['revision'],trust_remote_code=True,dtype=torch.bfloat16).to('cuda')
    model=PeftModel.from_pretrained(model,out/'adapter').eval()
    with torch.inference_mode():after=model(**probe,use_cache=False).logits[:,-1].float().cpu()
    dump(out/'reload.json',dict(exact=torch.equal(before,after),max_abs=float((before-after).abs().max())))
    assert torch.equal(before,after),'Reload parity failed'
    generations=[]
    if mode=='smoke':
        for text in ['Write hello only.','2 + 3 = ?']:
            prompt=tok.apply_chat_template([dict(role='user',content=text)],tokenize=False,add_generation_prompt=True,enable_thinking=False)
            inp=tok(prompt,return_tensors='pt').to('cuda')
            with torch.inference_mode():generated=model.generate(**inp,max_new_tokens=48,do_sample=False,repetition_penalty=1.1,eos_token_id=124900,pad_token_id=tok.pad_token_id)
            answer=tok.decode(generated[0,inp['input_ids'].shape[1]:],skip_special_tokens=False);assert answer.strip();generations.append(dict(prompt=text,answer=answer))
    dump(out/'training-manifest.json',dict(status='passed',experiment=exp,mode=mode,steps=expected,
         dataset_sha256=sha(source),runner_sha256=sha(Path(__file__)),config_sha256=sha(BASE/exp/'config.json'),
         initial_nll=initial,final_nll=final,metrics=result.metrics,wall_seconds=time.monotonic()-start,
         gradients_finite_nonzero_steps=len(checks),reload_exact=True,smoke_generations=generations,
         packages={p:importlib.metadata.version(p) for p in ['torch','transformers','trl','peft','datasets','accelerate']},
         max_allocated_bytes=torch.cuda.max_memory_allocated(),gpu=torch.cuda.get_device_name(),
         adapter_files={p.name:sha(p) for p in (out/'adapter').iterdir() if p.is_file()}))
    print('PASSED',exp,mode,expected,flush=True)

if __name__=='__main__':
    os.environ.setdefault('HF_HOME','/workspace/.cache/huggingface');os.environ.setdefault('HF_HUB_DISABLE_XET','1')
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['audit','smoke','tiny-overfit','sft']);p.add_argument('--experiment',choices=EXPS,default=EXPS[0]);a=p.parse_args()
    train(a.experiment,a.mode)
