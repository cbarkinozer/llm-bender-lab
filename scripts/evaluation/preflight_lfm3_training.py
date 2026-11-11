"""CPU random-weight TRL/PEFT compatibility and all-token label audit."""
import argparse
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--experiment-dir',type=Path,required=True)
    parser.add_argument('--scratch-dir',type=Path,required=True)
    args=parser.parse_args()
    import torch
    from datasets import Dataset
    from transformers import AutoConfig,AutoModelForCausalLM,AutoTokenizer
    from peft import LoraConfig
    from trl import SFTConfig,SFTTrainer
    cfg=json.loads((args.experiment_dir/'config-planned.json').read_text())['model']
    c=AutoConfig.from_pretrained(cfg['repo'],revision=cfg['revision'],code_revision=cfg['revision'],trust_remote_code=True)
    for k,v in dict(hidden_size=32,intermediate_size=64,num_hidden_layers=3,num_attention_heads=4,
        num_key_value_heads=2,head_dim=8,layer_types=['conv','sliding_attention','full_attention']).items():
        setattr(c,k,v)
    tokenizer=AutoTokenizer.from_pretrained(cfg['repo'],revision=cfg['revision'])
    model=AutoModelForCausalLM.from_config(c,code_revision=cfg['revision'],trust_remote_code=True)
    dataset=Dataset.from_list([dict(text='Bu metin yalnızca eğitim altyapısını denetlemek için hazırlanmıştır. '*15),
        dict(text='Deneme sırasında gerçek model ağırlıkları kullanılmaz ve sonuç başarı ölçümü değildir. '*15)])
    trainer=SFTTrainer(model=model,processing_class=tokenizer,train_dataset=dataset,
        peft_config=LoraConfig(r=4,lora_alpha=4,target_modules=['q_proj','k_proj','v_proj','o_proj','in_proj','out_proj','w1','w2','w3'],task_type='CAUSAL_LM'),
        args=SFTConfig(output_dir=str(args.scratch_dir),use_cpu=True,bf16=False,fp16=False,
            max_length=64,packing=True,packing_strategy='wrapped',completion_only_loss=False,
            dataset_text_field='text',report_to='none',per_device_train_batch_size=1,
            dataloader_num_workers=0,dataset_num_proc=1,max_steps=1,logging_steps=1,save_strategy='no'))
    batch=next(iter(trainer.get_train_dataloader()))
    labels=batch['labels']
    active=batch.get('attention_mask',torch.ones_like(labels)).bool()
    if not torch.equal(labels[active],batch['input_ids'][active]):
        raise ValueError('CPT must supervise every nonpadding raw-text token')
    if not torch.all(labels[~active]==-100):
        raise ValueError('Padding must not contribute loss')
    loss=trainer.compute_loss(trainer.model,batch)
    if not torch.isfinite(loss):
        raise ValueError('Nonfinite CPU CPT loss')
    loss.backward()
    gradients=[p.grad for p in trainer.model.parameters() if p.requires_grad and p.grad is not None]
    if not gradients or not all(torch.isfinite(g).all() for g in gradients) or not any(g.abs().sum()>0 for g in gradients):
        raise ValueError('LoRA gradients absent or invalid')
    report=dict(status='cpu_random_model_trl_peft_labels_and_backward_pass',
        supervised_tokens=int((labels!=-100).sum()),padding_tokens=int((~active).sum()),
        loss=float(loss.detach()),lora_gradient_tensors=len(gradients),
        caveat='Random tiny architecture only; actual 1.7B BF16 labels, training smoke and tiny-overfit remain GPU gates')
    (args.experiment_dir/'training-cpu-preflight-v01.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':
    main()
