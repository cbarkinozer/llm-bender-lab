"""exp-000 / exp-001: grounded QA with DPO on LFM3-1.7B ("answer from the documents or say you cannot").

Data: LiquidAI/grounded-qa (Apache-2.0), pinned revision. train has preference pairs (prompt, chosen, rejected); test and test_unseen
(domains never seen in training) are scored by rules, no judge model. Non-reasoning mode (enable_thinking=False), greedy decoding with
repetition_penalty 1.1 (the model card's recommendation), max 256 new tokens.
Per question the verdict is:
  answerable:   correct = contains the gold answer and not the fallback sentence; declined = answer is exactly the fallback
  unanswerable: correct = answer is exactly the fallback; fallback_then_answered = starts with the fallback, then adds an answer
Training (default = the Liquid notebook's recipe): LoRA r16/alpha32/dropout .05 on attention, conv and MLP projections, loss
sigmoid-DPO + SFT on the chosen answers (weights 1, 1), beta .1, LR 2e-5 cosine, 1 epoch, batch 2 x 8 accumulation, max length 3072.
  python scripts/training/run_pref_dpo_grounded_qa.py --out DIR --eval-only      # exp-000: untouched model
  python scripts/training/run_pref_dpo_grounded_qa.py --out DIR                  # exp-001: eval, train, eval
Smoke test on CPU: add --device cpu --n 2 --limit-train 4 --max-new-tokens 16 --max-length 1024.
"""
import argparse
import gc
import json
import random
import time
from pathlib import Path

import pref_rl_common as C

DATASET = 'LiquidAI/grounded-qa'
DATASET_REVISION = 'eb449523389ebfe24a9255fd7a5a90ead32ad4de'
SPLITS = ('test', 'test_unseen')
SYSTEM = ("Use only the documents the user provides to answer their question. Reply in the language of the question, in at most two "
          "sentences. When the documents do not contain the answer, reply with exactly the following sentence and nothing else: {fallback}")
TARGETS = ['q_proj', 'k_proj', 'v_proj', 'o_proj', 'in_proj', 'out_proj', 'w1', 'w2', 'w3']


def messages(row):
    docs = '\n\n'.join(f"[{i}] {d['title']}\n{d['text']}" for i, d in enumerate(row['documents'], start=1))
    return [{'role': 'system', 'content': SYSTEM.format(fallback=row['fallback'])},
            {'role': 'user', 'content': f"Documents:\n\n{docs}\n\nQuestion: {row['question']}"}]


def norm(text):
    return ' '.join(text.casefold().replace('’', "'").split()).strip(' .!?。')


def verdict(answer, row):
    """Classify one answer; returns a dict of booleans."""
    a, fb = norm(answer), norm(row['fallback'])
    declined = a == fb
    if row['answerable']:
        correct = fb not in a and norm(row['answer']) in a
        return dict(correct=correct, declined=declined, wrong=not correct and not declined)
    return dict(correct=declined, fallback_then_answered=(not declined) and a.startswith(fb),
                answered_without_fallback=(not declined) and not a.startswith(fb))


def evaluate(model, tok, rows, device, batch_size, max_new_tokens):
    import torch
    model.eval()
    out = []
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        prompts = [tok.apply_chat_template(messages(r), add_generation_prompt=True, tokenize=False, enable_thinking=False) for r in batch]
        enc = tok(prompts, return_tensors='pt', padding=True, add_special_tokens=False).to(device)
        with torch.inference_mode():
            gen = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False, repetition_penalty=1.1)
        for row, ids in zip(batch, gen[:, enc['input_ids'].shape[1]:]):
            answer = tok.decode(ids, skip_special_tokens=True).strip()
            out.append(dict(id=row['id'], language=row['language'], answerable=row['answerable'], answer=answer, **verdict(answer, row)))
        print(f'  evaluated {len(out)}/{len(rows)}', flush=True)
    return out


def summarize(outs):
    """Rates for one split from per-question outputs."""
    ans = [o for o in outs if o['answerable']]
    una = [o for o in outs if not o['answerable']]
    return {'answerable_correct': C.rate([o['correct'] for o in ans]), 'answerable_declined': C.rate([o['declined'] for o in ans]),
            'unanswerable_declined': C.rate([o['correct'] for o in una]),
            'unanswerable_fallback_then_answered': C.rate([o['fallback_then_answered'] for o in una]),
            'unanswerable_answered_without_fallback': C.rate([o['answered_without_fallback'] for o in una])}


def run_eval(tag, model, tok, data, args, device, out_dir):
    results = {}
    for split in SPLITS:
        rows = data[split]
        outs = evaluate(model, tok, rows, device, args.batch_size, args.max_new_tokens)
        C.write_jsonl(out_dir / f'eval-{tag}-{split}.jsonl', outs)
        results[split] = summarize(outs)
        print(tag, split, json.dumps({k: (None if v['rate'] is None else round(v['rate'], 3)) for k, v in results[split].items()}), flush=True)
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--eval-only', action='store_true', help='exp-000: evaluate the untouched model, no training')
    ap.add_argument('--device', default='auto')
    ap.add_argument('--n', type=int, default=0, help='Questions per test split (0 = the whole split), drawn with a fixed seed')
    ap.add_argument('--batch-size', type=int, default=16)
    ap.add_argument('--max-new-tokens', type=int, default=256)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--lr', type=float, default=2e-5)
    ap.add_argument('--beta', type=float, default=0.1)
    ap.add_argument('--rank', type=int, default=16)
    ap.add_argument('--epochs', type=float, default=1.0)
    ap.add_argument('--max-length', type=int, default=3072)
    ap.add_argument('--limit-train', type=int, default=0, help='Smoke test: first N training pairs only')
    ap.add_argument('--sft-weight', type=float, default=1.0, help='Weight of the SFT-on-chosen loss next to sigmoid DPO (0 = DPO only)')
    ap.add_argument('--tiny-test', action='store_true', help='Pipeline test with a random miniature model (no real results)')
    args = ap.parse_args()
    C.check_pins()
    import torch
    from datasets import Dataset, load_dataset
    from peft import LoraConfig, PeftModel
    from transformers import TrainerCallback, set_seed
    from trl import DPOConfig, DPOTrainer

    assert not args.out.exists(), 'Preserve the existing attempt'
    args.out.mkdir(parents=True)
    device, dtype = C.pick_device(args.device)
    set_seed(args.seed)
    tok = C.load_tokenizer()
    ds = load_dataset(DATASET, revision=DATASET_REVISION)
    data = {}
    for split in SPLITS + ('showcase',):
        rows = [dict(r) for r in ds[split]]
        if args.n and split in SPLITS:
            rows = random.Random(args.seed).sample(rows, min(args.n, len(rows)))
        data[split] = rows
    manifest: dict = dict(dataset=DATASET, dataset_revision=DATASET_REVISION, model=C.MODEL, model_revision=C.MODEL_REVISION, args={k: str(v) for k, v in vars(args).items()},
                    eval_rows={s: len(data[s]) for s in SPLITS}, runner_sha256=C.sha256_file(__file__), environment=C.environment(device))
    start = time.monotonic()
    model = C.load_model(device, dtype, tiny=args.tiny_test)
    manifest['attn_implementation'] = getattr(model.config, '_attn_implementation', None)
    baseline = run_eval('original', model, tok, data, args, device, args.out)
    manifest['original'] = baseline
    if args.eval_only:
        manifest['wall_seconds'] = time.monotonic() - start
        C.write_json(args.out / 'results.json', manifest)
        print('EVAL ONLY DONE')
        return

    pairs = [dict(prompt=messages(r), chosen=[{'role': 'assistant', 'content': r['chosen']}],
                  rejected=[{'role': 'assistant', 'content': r['rejected']}], chat_template_kwargs={'enable_thinking': False})
             for r in ds['train']]
    if args.limit_train:
        pairs = pairs[:args.limit_train]
    manifest['train_pairs'] = len(pairs)
    # pairs whose prompt plus longer answer exceeds max_length are cut by TRL's truncation; count them (1 of 4,072 at 3,072 tokens)
    over = 0
    for p in pairs:
        n_prompt = len(tok(tok.apply_chat_template(p['prompt'], add_generation_prompt=True, tokenize=False, enable_thinking=False),
                           add_special_tokens=False).input_ids)
        n_answer = max(len(tok(p[k][0]['content'], add_special_tokens=False).input_ids) for k in ('chosen', 'rejected')) + 2
        over += n_prompt + n_answer > args.max_length
    manifest['pairs_over_max_length'] = over
    manifest['rejected_types'] = {t: sum(r['rejected_type'] == t for r in list(ds['train'])[:len(pairs)]) for t in ('hallucination', 'refusal', 'wrong_answer')}
    cfg = DPOConfig(output_dir=str(args.out / 'trainer'), num_train_epochs=args.epochs, per_device_train_batch_size=2, gradient_accumulation_steps=8,
                    learning_rate=args.lr, loss_type=['sigmoid', 'sft'], loss_weights=[1.0, args.sft_weight], lr_scheduler_type='cosine',
                    warmup_steps=0.1, beta=args.beta, max_length=args.max_length, logging_steps=5, save_strategy='no', eval_strategy='no',
                    bf16=dtype == torch.bfloat16, use_cpu=device == 'cpu', seed=args.seed, data_seed=args.seed, report_to='none',
                    dataloader_num_workers=0)
    peft_config = LoraConfig(r=args.rank, lora_alpha=2 * args.rank, lora_dropout=0.05, target_modules=TARGETS, task_type='CAUSAL_LM')
    checks = []

    class FiniteGradients(TrainerCallback):
        def on_pre_optimizer_step(self, a, state, control, model=None, **k):
            grads = [p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
            assert grads and all(bool(torch.isfinite(g).all()) for g in grads), 'non-finite gradient'
            checks.append(state.global_step)

    trainer = DPOTrainer(model=model, args=cfg, train_dataset=Dataset.from_list(pairs), processing_class=tok, peft_config=peft_config,
                         callbacks=[FiniteGradients()])
    trainable = sum(p.numel() for p in trainer.model.parameters() if p.requires_grad)
    manifest['trainable_parameters'] = trainable
    t0 = time.monotonic()
    result = trainer.train()
    manifest['train'] = dict(metrics=result.metrics, steps=trainer.state.global_step, finite_gradient_steps=len(checks),
                             wall_seconds=time.monotonic() - t0, log_history=trainer.state.log_history,
                             peak_gpu_gb=(torch.cuda.max_memory_reserved() / 1e9 if device == 'cuda' else None))
    assert len(checks) == trainer.state.global_step, 'gradient check did not run on every step'
    manifest['learning_check'] = C.learning_check(trainer.state.log_history, 'dpo')
    print('LEARNING CHECK', json.dumps(manifest['learning_check']), flush=True)
    trainer.save_model(str(args.out / 'adapter'))
    tuned = trainer.model
    final = run_eval('trained', tuned, tok, data, args, device, args.out)
    manifest['trained'] = final
    # original vs fine-tuned on the hand-checked showcase questions (adapter switched off for the original)
    show = []
    for row in data['showcase']:
        one = {}
        for tag, off in (('original', True), ('trained', False)):
            if off:
                with tuned.disable_adapter():
                    one[tag] = evaluate(tuned, tok, [row], device, 1, args.max_new_tokens)[0]
            else:
                one[tag] = evaluate(tuned, tok, [row], device, 1, args.max_new_tokens)[0]
        show.append(dict(id=row['id'], language=row['language'], question=row['question'], answerable=row['answerable'],
                         reference=row['reference_answer'], original=one['original']['answer'], trained=one['trained']['answer'],
                         original_correct=one['original']['correct'], trained_correct=one['trained']['correct']))
    C.write_json(args.out / 'showcase.json', show)
    # save/reload parity of the adapter
    probe = tok('A short save and reload test.', return_tensors='pt').to(device)
    tuned.eval()
    with torch.inference_mode():
        before = tuned(**probe, use_cache=False).logits[:, -1].float().cpu()
    del trainer, tuned, model
    gc.collect()
    if device == 'cuda':
        torch.cuda.empty_cache()
    if not args.tiny_test:  # a random miniature cannot be rebuilt identically
        reloaded = PeftModel.from_pretrained(C.load_model(device, dtype), str(args.out / 'adapter')).eval()
        with torch.inference_mode():
            after = reloaded(**probe, use_cache=False).logits[:, -1].float().cpu()
        assert torch.equal(before, after), 'Reload parity failed'
        manifest['reload_exact'] = True
    manifest['adapter_files'] = {p.name: C.sha256_file(p) for p in (args.out / 'adapter').iterdir() if p.is_file()}
    manifest['wall_seconds'] = time.monotonic() - start
    C.write_json(args.out / 'results.json', manifest)
    print('PASSED')


if __name__ == '__main__':
    main()
