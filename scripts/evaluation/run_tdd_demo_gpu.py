"""GPU demo stages. Import engines lazily; do not execute model-generated code."""
import argparse
import importlib.metadata
import json
import math
import os
from pathlib import Path
import subprocess
import time
from active_tdd_data import EXP, ROOT, read_json, rows
from prepare_tdd_demo import digest, save, lines
from prepare_tdd_pair import arm_fields,inference_identity


def collate(features, pad_id):
    width=max(len(f['input_ids']) for f in features)
    return {k:[f[k]+[(-100 if k=='labels' else 0 if k=='attention_mask' else pad_id)]*(width-len(f[k])) for f in features]
            for k in ('input_ids','attention_mask','labels')}


def verify_preflight(preflight):
    manifest=read_json(preflight/'manifest.json')
    for name,expected in manifest['files'].items():
        if digest(preflight/name)!=expected: raise ValueError('Changed preflight '+name)
    for name,expected in manifest['source_inputs'].items():
        if digest(ROOT/name)!=expected: raise ValueError('Active input changed '+name)
    return read_json(preflight/'recipe.json')


def verified_stop_ids(tokenizer, expected):
    ids=[]
    for token in ('<|im_end|>','<|endoftext|>'):
        value=tokenizer.convert_tokens_to_ids(token)
        if value is None or value==tokenizer.unk_token_id or tokenizer.encode(token,add_special_tokens=False)!=[value]:
            raise ValueError('Native stop token is not a single known token: '+token)
        ids.append(value)
    if ids!=expected or tokenizer.eos_token_id!=ids[0]:raise ValueError('Stop-token mapping differs from pinned protocol')
    return ids


def runtime_signature():
    return {name:importlib.metadata.version(name) for name in ('vllm','torch','transformers','tokenizers')}


def gate_identity_matches(result,stage,preflight,config):
    if stage=='baseline':return result.get('inference_identity')==inference_identity(preflight,config)
    return result.get('recipe_sha256')==digest(preflight/'recipe.json')


def causal_token_loss(outputs,labels,num_items_in_batch=None):
    import torch.nn.functional as F
    logits=outputs['logits']
    if logits is None:raise ValueError('Explicit normalized loss requires returned logits')
    target=labels[...,1:].contiguous()
    count=int((target!=-100).sum())
    denominator=num_items_in_batch if num_items_in_batch is not None else count
    if int(denominator)<count or count==0:raise ValueError('Invalid token-loss denominator')
    # Chunk CE to avoid allocating a full sequence*vocabulary float32 copy.
    prediction=logits[...,:-1,:].reshape(-1,logits.shape[-1]);target=target.reshape(-1)
    loss=sum(F.cross_entropy(prediction[i:i+128].float(),target[i:i+128],ignore_index=-100,reduction='sum')
             for i in range(0,len(target),128))
    return loss/denominator


def generate(args, config):
    from vllm import LLM, SamplingParams
    from transformers import AutoTokenizer
    m=config['model'];g=config['inference']
    tokenizer=AutoTokenizer.from_pretrained(m['name'],revision=m['revision'])
    stop_ids=verified_stop_ids(tokenizer,g['stop_token_ids'])
    if args.runtime_lock is None:raise ValueError('Capture a runtime lock before any measured inference')
    lock=read_json(args.runtime_lock)
    if lock['packages']!=runtime_signature():raise ValueError('Inference environment differs from frozen runtime lock')
    requests=rows(args.preflight/'development-requests.jsonl')
    prompts=[tokenizer.apply_chat_template(r['messages'],tokenize=False,add_generation_prompt=True,enable_thinking=True) for r in requests]
    options=dict(model=m['name'],revision=m['revision'],dtype=g['dtype'],max_model_len=g['max_model_len'],
                 gpu_memory_utilization=.80,max_num_seqs=1,enable_lora=True,max_lora_rank=16,
                 seed=g['seed'],enable_chunked_prefill=False)
    for prompt in prompts:
        if len(tokenizer.encode(prompt,add_special_tokens=False))+g['max_tokens']>g['max_model_len']:
            raise ValueError('Prompt plus generation allowance exceeds model context')
    save(args.output/'generation-settings.json',dict(engine=options,sampling=g,verified_stop_token_ids=stop_ids,
         runtime_lock_sha256=digest(args.runtime_lock),packages=runtime_signature(),
         reproducibility='Greedy is not a guarantee of bitwise determinism; compare under same frozen runtime and request order'))
    llm=LLM(**options)
    adapter=None
    if args.adapter:
        evidence=read_json(args.adapter.parent/'result.json')
        if evidence['recipe_sha256']!=digest(args.preflight/'recipe.json'):
            raise ValueError('Adapter was trained under a different arm/recipe')
        from vllm.lora.request import LoRARequest
        adapter=LoRARequest('tdd-demo',1,str(args.adapter.resolve()))
    params=SamplingParams(temperature=0,max_tokens=g['max_tokens'],seed=g['seed'],
                          repetition_penalty=g['repetition_penalty'],stop_token_ids=stop_ids)
    started=time.monotonic()
    outputs=llm.generate(prompts,params,lora_request=adapter)
    if len(outputs)!=len(requests):raise ValueError('Missing generation outputs')
    records=[]
    for request,prompt,result in zip(requests,prompts,outputs):
        output=result.outputs[0]
        records.append(dict(record_id=request['record_id'],split=request['split'],capability=request['capability'],
                            prompt=prompt,prompt_token_ids=result.prompt_token_ids,text=output.text,
                            token_ids=list(output.token_ids),finish_reason=output.finish_reason,stop_reason=output.stop_reason))
    lines(args.output/'outputs.jsonl',records)
    if any(r['finish_reason'] not in ('stop','length') for r in records):raise ValueError('Unexpected generation failure')
    save(args.output/'result.json',dict(status='completed',stage='candidate' if args.adapter else 'baseline',
         recipe_sha256=digest(args.preflight/'recipe.json'),requests=len(records),seconds=time.monotonic()-started,
         truncated=sum(r['finish_reason']=='length' for r in records),adapter=str(args.adapter) if args.adapter else None,
         runtime_lock_sha256=digest(args.runtime_lock),outputs_sha256=digest(args.output/'outputs.jsonl'),
         inference_identity=inference_identity(args.preflight,config),arm=config.get('arm','A'),
         adapter_reload_verified=bool(args.adapter),runtime_execution=False))


def train(args, config):
    if args.mode=='full':
        if args.baseline is None:raise ValueError('Baseline run is required')
        if args.baseline_review is None:raise ValueError('Inspect baseline headroom and execution preflight before full training')
        review=read_json(args.baseline_review)
        if review['baseline_outputs_sha256']!=digest(args.baseline/'outputs.jsonl') or not review['outputs_inspected'] or not review['proceed_with_diagnostic'] or not review.get('reason'):
            raise ValueError('Baseline review missing, mismatched or recommends stopping')
        if read_json(args.baseline/'result.json').get('truncated',0) and not review.get('truncation_analysis'):
            raise ValueError('Classify truncated baseline outputs: repetitive versus progressive reasoning')
        if args.execution_preflight is None:raise ValueError('Protected reference-control execution is required')
        execution=read_json(args.execution_preflight/'summary.json')
        if execution['outputs_sha256']!=digest(args.preflight/'executor-reference-controls.jsonl') or execution['reference_passes']!=5 or execution['kills']!=execution['faults'] or execution['faults']==0:
            raise ValueError('Protected executor/reference preflight failed or evidence mismatched')
        if not review.get('execution_summary'):raise ValueError('Review must link baseline protected execution summary')
        baseline_execution=read_json(Path(review['execution_summary']))
        if baseline_execution['outputs_sha256']!=digest(args.baseline/'outputs.jsonl') or baseline_execution['image_id']!=execution['image_id'] or baseline_execution['tasks']!=5:
            raise ValueError('Baseline execution evidence is missing or uses different image/outputs')
        for location,stage in ((args.baseline,'baseline'),(args.smoke,'smoke'),(args.tiny,'tiny')):
            if location is None:raise ValueError('Full requires baseline, smoke and tiny evidence')
            result=read_json(location/'result.json')
            identity_ok=gate_identity_matches(result,stage,args.preflight,config)
            if result['status']!='completed' or result['stage']!=stage or not identity_ok:
                raise ValueError('Invalid GPU gate '+stage)
            if stage=='tiny' and not result['loss_decreased']:raise ValueError('Tiny overfit did not improve')
        if args.reload is None or not read_json(args.reload/'result.json').get('adapter_reload_verified'):
            raise ValueError('Candidate generation from smoke adapter must verify reload before full')
        reload_result=read_json(args.reload/'result.json')
        if reload_result['recipe_sha256']!=digest(args.preflight/'recipe.json') or Path(reload_result['adapter']).resolve()!=(args.smoke/'adapter').resolve():
            raise ValueError('Reload evidence must refer to this recipe and smoke adapter')
    os.environ['UNSLOTH_RETURN_LOGITS']='1'
    from unsloth import FastLanguageModel
    import torch
    from datasets import Dataset
    from transformers import AutoTokenizer, Trainer, TrainingArguments, set_seed
    from native_tdd_labels import encode_conversation, model_fields
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():raise ValueError('BF16 GPU required')
    if int(os.environ.get('WORLD_SIZE','1'))!=1 or torch.cuda.device_count()!=1:
        raise ValueError('This token-normalized pilot is single-GPU; expose one device')
    t=config['training'];m=config['model'];l=t['lora'];set_seed(t['seed'])
    model,_=FastLanguageModel.from_pretrained(model_name=m['name'],revision=m['revision'],max_seq_length=t['max_seq_length'],
                                            load_in_4bit=False,load_in_16bit=True,full_finetuning=False)
    matches={suffix:[name for name,module in model.named_modules() if name.endswith('.'+suffix)] for suffix in l['target_modules']}
    if any(not values for values in matches.values()):raise ValueError('Requested LoRA suffix matched no modules')
    model=FastLanguageModel.get_peft_model(model,r=l['rank'],lora_alpha=l['alpha'],lora_dropout=l['dropout'],bias='none',
        target_modules=l['target_modules'],use_gradient_checkpointing='unsloth',random_state=t['seed'])
    save(args.output/'lora-modules.json',dict(matched_modules=matches,
         trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),
         total_parameters=sum(p.numel() for p in model.parameters()),
         scope='Requested suffix matches; not asserted to cover every linear or hybrid attention layer'))
    tokenizer=AutoTokenizer.from_pretrained(m['name'],revision=m['revision'])
    encoded=rows(args.preflight/'train-encoded.jsonl')
    # Re-encode with the actual GPU environment's tokenizer and verify every array.
    from active_tdd_data import active_paths
    from export_intent_only_preview import project_record
    source=[r for r in rows(active_paths()['tests']) if r['candidate_split']=='train']
    for row,saved in zip(source,encoded):
        full=encode_conversation(tokenizer,project_record(row)['messages'],max_length=t['max_seq_length'])
        fresh=arm_fields(full,config.get('arm','A'))
        if fresh!={k:saved[k] for k in fresh}:raise ValueError('GPU tokenizer/label parity failure')
    if len(source)!=len(encoded):raise ValueError('Row mismatch')
    if args.mode=='tiny':encoded=encoded[:4]
    data=Dataset.from_list([{k:r[k] for k in ('input_ids','attention_mask','labels')} for r in encoded])
    def collator(features):return {k:torch.tensor(v,dtype=torch.long) for k,v in collate(features,tokenizer.pad_token_id).items()}
    class CheckedTrainer(Trainer):
        def training_step(self,model,inputs,*a,**kw):
            # Compare actual trainer microbatches to saved arrays, without relying on row order.
            known={tuple(r['input_ids']):r['labels'] for r in encoded}
            for ids,attention,labels in zip(inputs['input_ids'],inputs['attention_mask'],inputs['labels']):
                n=int(attention.sum());key=tuple(ids[:n].tolist())
                if key not in known or labels[:n].tolist()!=known[key] or (labels[n:]!=-100).any():
                    raise ValueError('Actual training batch labels changed')
            loss=super().training_step(model,inputs,*a,**kw)
            with (args.output/'exposure.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(dict(step=self.state.global_step,input_tokens=int(inputs['attention_mask'].sum()),
                                             supervised_tokens=int((inputs['labels']!=-100).sum())))+'\n')
            return loss
    ta=TrainingArguments(output_dir=str(args.output/'checkpoints'),per_device_train_batch_size=1,
        gradient_accumulation_steps=1 if args.mode=='tiny' else t['gradient_accumulation_steps'],
        num_train_epochs=t['epochs'],max_steps=3 if args.mode=='smoke' else 20 if args.mode=='tiny' else -1,
        learning_rate=2e-4 if args.mode=='tiny' else t['learning_rate'],optim=t['optimizer'],
        lr_scheduler_type=t['scheduler'],warmup_steps=t['warmup_steps'],weight_decay=t['weight_decay'],max_grad_norm=t['max_grad_norm'],
        bf16=True,fp16=False,seed=t['seed'],data_seed=t['seed'],logging_steps=1,save_strategy='no',
        report_to=[],remove_unused_columns=False,prediction_loss_only=True)
    def checked_loss(outputs,labels,num_items_in_batch=None):
        if model.training and num_items_in_batch is None:raise ValueError('Trainer omitted accumulation-group token count')
        if model.training:
            with (args.output/'loss-normalization.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(dict(microbatch_tokens=int((labels[...,1:]!=-100).sum()),
                                             accumulation_group_tokens=int(num_items_in_batch)))+'\n')
        return causal_token_loss(outputs,labels,num_items_in_batch)
    trainer=CheckedTrainer(model=model,args=ta,train_dataset=data,data_collator=collator,compute_loss_func=checked_loss)
    batch=next(iter(trainer.get_train_dataloader()))
    assert (batch['labels']!=-100).any()
    save(args.output/'actual-first-batch.json',{k:v.tolist() for k,v in batch.items()})
    before=trainer.evaluate(eval_dataset=data)['eval_loss'] if args.mode=='tiny' else None
    result=trainer.train()
    after=trainer.evaluate(eval_dataset=data)['eval_loss'] if args.mode=='tiny' else None
    if not math.isfinite(result.training_loss):raise ValueError('Nonfinite loss')
    trainer.save_model(str(args.output/'adapter'));tokenizer.save_pretrained(args.output/'adapter')
    save(args.output/'training-arguments.json',ta.to_dict())
    save(args.output/'result.json',dict(status='completed',stage=args.mode,recipe_sha256=digest(args.preflight/'recipe.json'),
        metrics=result.metrics,before=before,after=after,loss_decreased=after<before if before is not None else None,
        actual_batch_labels_verified=True,adapter_reload_verified=False))


def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['baseline','candidate','smoke','tiny','full'],required=True)
    p.add_argument('--preflight',type=Path,default=EXP/'paired-preflight-v01/A');p.add_argument('--output',type=Path,required=True)
    for key in ('adapter','baseline','smoke','tiny','reload','runtime-lock','baseline-review','execution-preflight'):p.add_argument('--'+key,type=Path)
    args=p.parse_args();config=verify_preflight(args.preflight)
    if args.mode=='candidate' and args.adapter is None:raise ValueError('Candidate requires adapter')
    if args.mode=='baseline' and args.adapter:raise ValueError('Baseline must be untouched base')
    if args.output.exists():raise ValueError('Preserve run directories')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('Commit source before GPU run')
    args.output.mkdir(parents=True)
    save(args.output/'environment.json',dict(git=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
         packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions()},mode=args.mode))
    if args.mode in ('baseline','candidate'):generate(args,config)
    else:train(args,config)


if __name__=='__main__':main()
