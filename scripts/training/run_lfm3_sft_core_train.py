"""SFT core v01: LoRA SFT of LFM3 on a pack file (the model's own verified answers), exp-016 recipe at pack scale.

LoRA r32/alpha64 (exp-014 config), LR 1e-4 cosine with 6 warmup steps, effective batch 8 (1 x 8 accumulation), completion-only
loss through native TRL, max_length 8192 (exp-016's 4096 cut long reasoning), shuffled with a fixed seed.
Pack rows: {prompt, completion, chat_template_kwargs, tools?}. Tools go to TRL as a JSON string (nested schemas differ per row,
which Arrow cannot hold as structs). Audits: prompt tokens masked, EOS supervised, no think tags in direct rows, a closed think
block in reasoning rows, tool names present in the rendered prompt, zero truncation, finite gradients, adapter reload parity.
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
EOS_ID = 124900
KEYS = ('prompt', 'completion', 'chat_template_kwargs', 'tools')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--parent', help='Merged parent model directory (default: the pinned original base)')
    parser.add_argument('--epochs', type=float, default=1.0)
    parser.add_argument('--lr', type=float, default=1e-4)
    parser.add_argument('--max-length', type=int, default=8192)
    parser.add_argument('--limit', type=int, help='Smoke test: first N rows only')
    parser.add_argument('--audit-only', action='store_true', help='Tokenize and audit, do not train')
    parser.add_argument('--seed', type=int, default=3407, help='Training seed (data order and LoRA init); 3407 reproduces exp-019')
    args = parser.parse_args()
    os.environ.setdefault('HF_HOME', '/workspace/.cache/huggingface')
    import torch
    from datasets import Dataset
    from peft import LoraConfig, PeftModel, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainerCallback, set_seed
    from trl import SFTConfig, SFTTrainer

    exp014 = read(BASE / 'exp-014-completion-mask/config.json')
    model_cfg = exp014['model']
    old = read(BASE / 'exp-012-base-bilingual/config.yaml')['training']
    rows = [json.loads(s) for s in args.data.read_text(encoding='utf-8').split('\n') if s.strip()]
    if args.limit:
        rows = rows[:args.limit]
    data = [{k: (json.dumps(r[k], ensure_ascii=False) if k == 'tools' and r.get(k) else r.get(k)) for k in KEYS} for r in rows]
    steps = max(1, round(len(data) * args.epochs / 8))
    assert not args.out.exists(), 'Preserve the existing attempt'
    args.out.mkdir(parents=True)
    set_seed(args.seed)
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
    cfg = SFTConfig(output_dir=str(args.out), per_device_train_batch_size=1, gradient_accumulation_steps=8,
                    learning_rate=args.lr, max_length=args.max_length, completion_only_loss=True, assistant_only_loss=False,
                    packing=False, bf16=True, fp16=False, gradient_checkpointing=True,
                    gradient_checkpointing_kwargs={'use_reentrant': False}, seed=args.seed, data_seed=args.seed, logging_steps=5,
                    save_strategy='no', eval_strategy='no', report_to='none', dataloader_num_workers=0, optim=old['optimizer'],
                    weight_decay=old['weight_decay'], adam_beta1=old['adam_beta1'], adam_beta2=old['adam_beta2'],
                    adam_epsilon=old['adam_epsilon'], max_grad_norm=old['max_grad_norm'], max_steps=steps,
                    warmup_steps=min(steps - 1, max(6, steps // 16)), lr_scheduler_type='cosine')
    checks = []

    class Check(TrainerCallback):
        def on_pre_optimizer_step(self, a, state, control, model=None, **k):
            grads = [p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
            assert grads and all(bool(torch.isfinite(g).all()) for g in grads)
            checks.append(state.global_step)

    trainer = SFTTrainer(model=model, args=cfg, train_dataset=Dataset.from_list(data), processing_class=tok,
                         callbacks=[Check()])
    prepared = trainer.train_dataset
    lengths = [len(x) for x in prepared['input_ids']]
    over = [i for i, n in enumerate(lengths) if n >= args.max_length]
    assert not over, f'{len(over)} rows reach max_length {args.max_length} (truncation): {over[:10]}'
    audits, supervised_total = [], 0
    for i in range(len(data)):
        ids, labels = prepared[i]['input_ids'], prepared[i]['labels']
        first = next(j for j, v in enumerate(labels) if v != -100)
        assert all(v == -100 for v in labels[:first]), (i, 'prompt tokens not masked')
        gaps = [j for j in range(first, len(labels)) if labels[j] != ids[j]]
        assert not gaps, (i, 'masked tokens inside the completion', gaps[:5])
        assert EOS_ID in labels[first:], (i, 'EOS not supervised')
        supervised_total += len(labels) - first
        if i % 5:
            continue
        target = tok.decode(ids[first:], skip_special_tokens=False)
        thinking = data[i]['chat_template_kwargs']['enable_thinking']
        if thinking:
            assert '</think>' in target, (i, 'reasoning row without a closed think block')
        else:
            assert '<think>' not in target and '</think>' not in target, (i, 'think tag in a direct row')
        if data[i]['tools']:
            names = [t['name'] for t in json.loads(data[i]['tools'])]
            prompt_text = tok.decode(ids[:first], skip_special_tokens=False)
            assert all(n in prompt_text for n in names), (i, 'tool names missing from the rendered prompt')
        audits.append(i)
    stats = dict(rows=len(data), steps=steps, tokens_total=sum(lengths), tokens_supervised=supervised_total,
                 max_tokens=max(lengths), median_tokens=sorted(lengths)[len(lengths) // 2], audited=len(audits))
    print('AUDITS PASSED', json.dumps(stats), flush=True)
    (args.out / 'audit.json').write_text(json.dumps(stats, indent=1) + '\n', encoding='utf-8')
    if args.audit_only:
        return
    start = time.monotonic()
    result = trainer.train()
    assert trainer.state.global_step == steps and len(checks) == steps
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
    manifest = dict(status='passed', steps=steps, epochs=args.epochs, lr=args.lr, max_length=args.max_length, parent=args.parent, seed=args.seed,
                    dataset_sha256=sha(args.data), runner_sha256=sha(Path(__file__)), metrics=result.metrics,
                    wall_seconds=time.monotonic() - start, reload_exact=True, stats=stats, gpu=torch.cuda.get_device_name(),
                    packages={p: importlib.metadata.version(p) for p in ('torch', 'transformers', 'trl', 'peft', 'datasets')},
                    adapter_files={p.name: sha(p) for p in (args.out / 'adapter').iterdir() if p.is_file()})
    (args.out / 'training-manifest.json').write_text(json.dumps(manifest, indent=1) + '\n', encoding='utf-8')
    print('PASSED', steps, flush=True)


if __name__ == '__main__':
    main()
