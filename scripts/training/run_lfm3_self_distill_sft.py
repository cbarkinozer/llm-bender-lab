"""exp-016: exp014's SFT recipe on self-distilled targets (only the targets differ).

Same base, LoRA r32/alpha64, LR 1e-4, batch 2 x accumulation 4, cosine warmup 6 with the 113-step horizon,
order.json (exp012 order_b filtered to kept groups, same per-row exposure as exp014; steps = entries / 8),
cosine horizon scaled so the stop point is the same fraction of the schedule as in exp014, sequential sampler, completion-only loss through native TRL.
Audits: prompt tokens masked, EOS supervised, no think tags in direct rows, finite gradients, reload parity.
"""
import argparse
import gc
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
TEMPLATE_SHA256 = 'f45005c50cd2a97329722bf3a2dee9f16c04cdf825a589b280fb7e99e6827818'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment', default='exp-016-self-distill-targets')
    parser.add_argument('--data', type=Path, help='Training file (default: <experiment>/train-selfdistill.jsonl)')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--parent', help='Merged parent model directory (default: the pinned original base)')
    parser.add_argument('--repeat', type=int, default=1, help='Repeat order.json this many times')
    parser.add_argument('--max-steps', type=int, help='Default: rows / 8 (one pass over the order file)')
    args = parser.parse_args()
    os.environ.setdefault('HF_HOME', '/workspace/.cache/huggingface')
    import torch
    from datasets import Dataset
    from peft import LoraConfig, PeftModel, get_peft_model
    from torch.utils.data import SequentialSampler
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainerCallback, set_seed
    from trl import SFTConfig, SFTTrainer

    exp014 = read(BASE / 'exp-014-completion-mask/config.json')
    model_cfg = exp014['model']
    source = args.data or BASE / args.experiment / 'train-selfdistill.jsonl'
    data = [json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
    order = read(BASE / args.experiment / 'order.json')
    assert min(order) >= 0 and max(order) < len(data) and len(order) % 8 == 0
    order = order * args.repeat
    args.max_steps = args.max_steps or len(order) // 8
    horizon = round(113 * args.max_steps / 69)  # exp014 stopped at 69 of a 113-step cosine horizon
    old = read(BASE / 'exp-012-base-bilingual/config.yaml')['training']
    assert not args.out.exists(), 'Preserve the existing attempt'
    args.out.mkdir(parents=True)
    set_seed(exp014['seed'])
    tok = AutoTokenizer.from_pretrained(model_cfg['repo'], revision=model_cfg['revision'], padding_side='left')
    assert hashlib.sha256(tok.chat_template.encode()).hexdigest() == TEMPLATE_SHA256
    def load_parent():
        if args.parent:
            return AutoModelForCausalLM.from_pretrained(args.parent, trust_remote_code=True, dtype=torch.bfloat16).to('cuda')
        return AutoModelForCausalLM.from_pretrained(model_cfg['repo'], revision=model_cfg['revision'],
                                                    code_revision=model_cfg['revision'], trust_remote_code=True,
                                                    dtype=torch.bfloat16).to('cuda')

    model = load_parent()
    model.config.use_cache = False
    model = get_peft_model(model, LoraConfig(r=exp014['r'], lora_alpha=exp014['lora_alpha'], lora_dropout=0.0,
                                             target_modules=exp014['target_modules'], task_type='CAUSAL_LM'))
    model.enable_input_require_grads()

    class Ordered(SFTTrainer):
        def _get_train_sampler(self, *a, **k):
            return SequentialSampler(self.train_dataset)

    cfg = SFTConfig(output_dir=str(args.out), per_device_train_batch_size=2, gradient_accumulation_steps=4,
                    learning_rate=exp014['learning_rate'], max_length=4096, completion_only_loss=True,
                    assistant_only_loss=False, packing=False, bf16=True, fp16=False, gradient_checkpointing=True,
                    gradient_checkpointing_kwargs={'use_reentrant': False}, seed=3407, data_seed=3407,
                    logging_steps=1, save_strategy='no', eval_strategy='no', report_to='none',
                    dataloader_num_workers=0, optim=old['optimizer'], weight_decay=old['weight_decay'],
                    adam_beta1=old['adam_beta1'], adam_beta2=old['adam_beta2'], adam_epsilon=old['adam_epsilon'],
                    max_grad_norm=old['max_grad_norm'], max_steps=horizon, warmup_steps=6, lr_scheduler_type='cosine')
    checks = []

    class Check(TrainerCallback):
        def on_step_end(self, a, state, control, **k):
            if state.global_step >= args.max_steps:
                control.should_training_stop = True
            return control

        def on_pre_optimizer_step(self, a, state, control, model=None, **k):
            grads = [p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
            assert grads and all(bool(torch.isfinite(g).all()) for g in grads)
            checks.append(state.global_step)

    trainer = Ordered(model=model, args=cfg, train_dataset=Dataset.from_list(data), processing_class=tok,
                      callbacks=[Check()])
    prepared = trainer.train_dataset
    audits = []
    for i in range(0, len(data), 7):
        batch = trainer.data_collator([prepared[i]])
        ids, labels = batch['input_ids'][0].tolist(), batch['labels'][0].tolist()
        first = next(j for j, v in enumerate(labels) if v != -100)
        assert all(v == -100 for v in labels[:first]), (i, 'prompt tokens not masked')
        gaps = [j for j in range(first, len(labels)) if labels[j] != ids[j]]
        assert not gaps, (i, 'masked tokens inside the completion', gaps[:5], len(labels) - first)
        assert 124900 in labels, (i, 'EOS not supervised')
        target = tok.decode([v for v in labels if v != -100], skip_special_tokens=False)
        if not data[i]['chat_template_kwargs']['enable_thinking']:
            assert '<think>' not in target and '</think>' not in target, i
        audits.append(dict(row=i, supervised=len(labels) - first))
    trainer.train_dataset = prepared.select(order)
    start = time.monotonic()
    result = trainer.train()
    assert trainer.state.global_step == args.max_steps and len(checks) == args.max_steps
    trainer.save_model(args.out / 'adapter')
    tok.save_pretrained(args.out / 'adapter')
    model = trainer.accelerator.unwrap_model(model, keep_fp32_wrapper=False).eval()
    probe = tok('A short save and reload test.', return_tensors='pt').to('cuda')
    with torch.inference_mode():
        before = model(**probe, use_cache=False).logits[:, -1].float().cpu()
    del trainer, model
    gc.collect()
    torch.cuda.empty_cache()
    model = load_parent()
    model = PeftModel.from_pretrained(model, args.out / 'adapter').eval()
    with torch.inference_mode():
        after = model(**probe, use_cache=False).logits[:, -1].float().cpu()
    assert torch.equal(before, after), 'Reload parity failed'
    manifest = dict(status='passed', experiment=args.experiment, steps=args.max_steps, parent=args.parent, repeat=args.repeat, dataset_sha256=sha(source),
                    runner_sha256=sha(Path(__file__)), metrics=result.metrics, wall_seconds=time.monotonic() - start,
                    reload_exact=True, mask_audits=len(audits), gpu=torch.cuda.get_device_name(),
                    packages={p: importlib.metadata.version(p) for p in ('torch', 'transformers', 'trl', 'peft', 'datasets')},
                    adapter_files={p.name: sha(p) for p in (args.out / 'adapter').iterdir() if p.is_file()})
    (args.out / 'training-manifest.json').write_text(json.dumps(manifest, indent=1) + '\n', encoding='utf-8')
    print('PASSED', args.max_steps, flush=True)


if __name__ == '__main__':
    main()
