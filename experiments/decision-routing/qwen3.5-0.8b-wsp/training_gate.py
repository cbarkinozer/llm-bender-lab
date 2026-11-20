"""Train-only tiny-overfit, gradient and reload gates before the real candidate run."""
import os
os.environ.update(UNSLOTH_DISABLE_STATISTICS='1',WANDB_MODE='disabled',TOKENIZERS_PARALLELISM='false')
import gc,hashlib,json,math
from pathlib import Path

def main():
    from unsloth import FastDecisionModel,DecisionTrainer
    import torch
    from datasets import Dataset
    from transformers import TrainingArguments,TrainerCallback,set_seed
    from decision_training_utils import check_build_report
    root=Path('/workspace/reflex-wsp');out=root/'runs/wsp-tiny-overfit';out.mkdir(parents=True,exist_ok=False)
    for arm in ['parent','wsp','released']:
        summary=json.loads((root/'eval/routing'/arm/'summary.json').read_text())
        assert len(summary)==4
        assert all(not v['build_report'].get('truncated',0) and not v['build_report'].get('skipped',0) for v in summary.values())
    models=json.loads((root/'models.json').read_text())
    selected=[];counts={}
    # Only training data; at most three examples from each source/route bucket.
    for row in map(json.loads,(root/'data/materialized/train-s3407.jsonl').read_text().splitlines()):
        key=(row.get('source','phone'),row.get('route__label',''))
        if counts.get(key,0)<1:
            selected.append(row);counts[key]=1
        if len(selected)==48:break
    assert len(selected)==48
    set_seed(3407)
    model,tok=FastDecisionModel.from_pretrained(model_name=models['wsp_training'],max_seq_length=4096,dtype=None,load_in_4bit=True)
    model=FastDecisionModel.get_peft_model(model,r=16,lora_alpha=16,lora_dropout=0,use_gradient_checkpointing='unsloth',random_state=3407)
    items,report=FastDecisionModel.build_dataset(Dataset.from_list(selected),tok,model)
    check_build_report(items,report,'tiny_train')
    # Soft-target argmax can disagree with the explicit hard label. Choose
    # compatible train rows for a memorization diagnostic without changing gold.
    compatible=[i for i,item in enumerate(items) if all(max(range(len(t)),key=t.__getitem__)==label for t,label in zip(item['targets'],item['labels']))][:24]
    assert len(compatible)==24
    selected=[selected[i] for i in compatible];items=[items[i] for i in compatible]
    (out/'train-only.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in selected))
    before=FastDecisionModel.evaluate(model,tok,items,batch_size=2)
    observations={'losses':[],'gradients':{},'optimizer_groups':[],'train_checks':[]}
    class Audit(TrainerCallback):
        def on_log(self,args,state,control,logs=None,**kwargs):
            if logs and 'loss' in logs:
                assert math.isfinite(logs['loss']);observations['losses'].append(logs['loss'])
        def on_pre_optimizer_step(self,args,state,control,model=None,optimizer=None,**kwargs):
            if state.global_step==0:
                for kind,needle in [('head','head.'),('lora','lora_')]:
                    value=sum(float(p.grad.detach().float().abs().sum()) for n,p in model.named_parameters() if needle in n and p.grad is not None)
                    assert math.isfinite(value) and value>0,(kind,value)
                    observations['gradients'][kind]=value
                observations['optimizer_groups']=[{'lr':g['lr'],'tensors':len(g['params'])} for g in optimizer.param_groups]
        def on_step_end(self,args,state,control,model=None,**kwargs):
            if state.global_step%20==0:
                metrics=FastDecisionModel.evaluate(model,tok,items,batch_size=2)
                observations['train_checks'].append({'step':state.global_step,**metrics})
                print('Tiny train-only check',state.global_step,metrics,flush=True)
                if metrics['accuracy']>=.95:control.should_training_stop=True
    trainer=DecisionTrainer(model=model,processing_class=tok,train_dataset=items,
        args=TrainingArguments(output_dir=str(out/'checkpoints'),per_device_train_batch_size=2,
            gradient_accumulation_steps=1,max_steps=160,learning_rate=2e-4,warmup_steps=0,
            bf16=True,logging_steps=5,save_strategy='no',eval_strategy='no',
            optim='adamw_8bit',weight_decay=0,lr_scheduler_type='constant',seed=3407,report_to='none'),callbacks=[Audit()])
    trainer.train()
    after=FastDecisionModel.evaluate(model,tok,items,batch_size=2)
    (out/'learning-check.json').write_text(json.dumps({'before':before,'after':after,'audit':observations},indent=2)+'\n')
    assert after['accuracy']>=.9 and after['loss']<before['loss'],(before,after)
    FastDecisionModel.for_inference(model)
    probe=selected[0];questions=json.loads(probe['questions'])
    prediction=FastDecisionModel.predict(model,tok,probe['state'],questions)
    model.save_pretrained(str(out/'adapter'));tok.save_pretrained(str(out/'adapter'))
    del trainer,model;gc.collect();torch.cuda.empty_cache()
    model,tok=FastDecisionModel.from_pretrained(model_name=str(out/'adapter'),max_seq_length=4096,dtype=None,load_in_4bit=True)
    FastDecisionModel.for_inference(model)
    reloaded=FastDecisionModel.predict(model,tok,probe['state'],questions)
    for key in prediction:
        assert prediction[key]['answer']==reloaded[key]['answer']
        p1=prediction[key]['probabilities'];p2=reloaded[key]['probabilities']
        assert max(abs(p1[k]-p2[k]) for k in p1)<.002,(prediction,reloaded)
    result={'passed':True,'before':before,'after':after,'reload_prediction':reloaded,'audit':observations,
        'train_ids':[r['id'] for r in selected],'purpose':'Train-only pipeline diagnostic on rows with compatible soft/hard labels; discarded before fresh candidate initialization'}
    (out/'gate.json').write_text(json.dumps(result,indent=2)+'\n');print('TRAINING GATES PASSED',flush=True)

if __name__=='__main__':main()
