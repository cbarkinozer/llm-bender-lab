"""exp-000 / exp-002: phone-assistant tool calling with GRPO on LFM3-1.7B (reward = the calls match the gold calls).

Data: LiquidAI/phone-assistant-tools (Apache-2.0), pinned revision: 108 tools in every prompt (about 8,100 tokens), requests in 16
languages. Splits: train (98 of the 108 tools), test (same tools), test_unseen (10 held-out tools, five of them lookalikes of training
tools). Scored by rule with scripts/evaluation/phone_tools_scoring.py (exact calls in any order, arguments compared by kind).
Non-reasoning mode, greedy decoding, max 512 new tokens.
Reward per sampled answer: 1.0 when the calls match the gold calls exactly (for no-call requests: when the model makes no call), else
0.2 x F1 of the tool names. Requests that need no call (no_tool, clarify) are shown twice, because only 15% of them would otherwise
make always-call-a-tool the winning strategy.
Training (default = the Liquid notebook's recipe): LoRA r32/alpha64 on attention, conv and MLP projections, 150 steps, 8 answers per
request, 32 answers per step, completion length 256, temperature 1, LR 1e-5 constant with 5 warmup steps, KL penalty beta .04.
  python scripts/training/run_pref_grpo_phone_tools.py --out DIR --eval-only     # exp-000: untouched model
  python scripts/training/run_pref_grpo_phone_tools.py --out DIR                 # exp-002: eval, train, eval
Pipeline test on CPU with a tiny random model (numbers meaningless): add --tiny-test --device cpu --n 4 --max-steps 1.
"""
import argparse
import contextlib
import gc
import json
import random
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import pref_rl_common as C

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'evaluation'))
import phone_tools_scoring as S  # noqa: E402

DATASET = 'LiquidAI/phone-assistant-tools'
DATASET_REVISION = '02100f57ab94eda248909b83a79e9d46a590d038'
SPLITS = ('test', 'test_unseen')
TARGETS = ['q_proj', 'k_proj', 'v_proj', 'o_proj', 'in_proj', 'out_proj', 'w1', 'w2', 'w3']
SYSTEM = """You are an assistant running on the user's phone, with access to the phone's tools.
Current date and time: {weekday}, {date} {time} ({timezone}). User locale: {locale}.

Rules:
- Make every tool call the request needs, with arguments taken from the request and the context above. Set an optional argument only when the user gives it, and never invent values.
- Work out relative dates and times ("tomorrow", "on Friday", "in 20 minutes") from the current date and time. Times are local, in the formats the tool descriptions state.
- When a required detail is missing, ask one short clarifying question instead of calling a tool.
- Answer small talk and general-knowledge questions directly, without tools. Use translate_text, calculate, convert_units and convert_currency for translations, arithmetic and conversions, and search_web or get_news_headlines for current or local information.
- When no tool can do what was asked, say so briefly instead of calling a different tool. When only part of the request is possible, do that part and say what you could not do.
- Write free-text arguments (messages, notes, search queries) in the user's language."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--eval-only', action='store_true', help='exp-000: evaluate the untouched model, no training')
    ap.add_argument('--device', default='auto')
    ap.add_argument('--n', type=int, default=0, help='Requests per test split (0 = the whole split), drawn with a fixed seed')
    ap.add_argument('--batch-size', type=int, default=8)
    ap.add_argument('--max-new-tokens', type=int, default=512)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--max-steps', type=int, default=150)
    ap.add_argument('--lr', type=float, default=1e-5)
    ap.add_argument('--beta', type=float, default=0.04)
    ap.add_argument('--rank', type=int, default=32)
    ap.add_argument('--num-generations', type=int, default=8)
    ap.add_argument('--max-completion-length', type=int, default=256)
    ap.add_argument('--limit-train', type=int, default=0, help='Smoke test: first N training requests only')
    ap.add_argument('--tiny-test', action='store_true', help='Pipeline test with a random miniature model (no real results)')
    args = ap.parse_args()
    if not args.tiny_test:
        C.check_pins()
    import torch
    from datasets import Dataset, load_dataset
    from huggingface_hub import hf_hub_download
    from peft import LoraConfig, PeftModel
    from transformers import TrainerCallback, set_seed
    from trl import GRPOConfig, GRPOTrainer

    assert not args.out.exists(), 'Preserve the existing attempt'
    args.out.mkdir(parents=True)
    device, dtype = C.pick_device(args.device)
    set_seed(args.seed)
    tok = C.load_tokenizer()
    tools = json.loads(Path(hf_hub_download(DATASET, 'tools.json', repo_type='dataset', revision=DATASET_REVISION)).read_text(encoding='utf-8'))
    kinds = json.loads(Path(hf_hub_download(DATASET, 'scoring.json', repo_type='dataset', revision=DATASET_REVISION)).read_text(encoding='utf-8'))
    scorer = S.Scorer(tools, kinds)
    prompt_tools = tools[:12] if args.tiny_test else tools  # the pipeline test uses a short tool list (CPU), scoring still knows all tools
    ds = load_dataset(DATASET, revision=DATASET_REVISION)

    def build_prompt(row):
        now = datetime.fromisoformat(row['context']['datetime'])
        system = SYSTEM.format(weekday=now.strftime('%A'), date=now.strftime('%Y-%m-%d'), time=now.strftime('%H:%M'), **row['context'])
        msgs = [{'role': 'system', 'content': system}, {'role': 'user', 'content': row['request']}]
        return tok.apply_chat_template(msgs, tools=prompt_tools, add_generation_prompt=True, tokenize=False, enable_thinking=False)

    parse_errors = Counter()

    def parse_calls(ids, prompt):
        """Calls in a completion; a completion the parser cannot read counts as no call (and is counted)."""
        ids = [int(i) for i in ids if int(i) != tok.pad_token_id]
        try:
            message = tok.parse_response(ids, prefix=prompt, tools=prompt_tools)
        except Exception as e:  # malformed tool-call text
            parse_errors[type(e).__name__] += 1
            return []
        return [c['function'] for c in message.get('tool_calls') or []]

    def evaluate(model, tag, split_rows):
        model.eval()
        results = {}
        for split, rows in split_rows.items():
            outs = []
            for start in range(0, len(rows), args.batch_size):
                batch = rows[start:start + args.batch_size]
                prompts = [build_prompt(r) for r in batch]
                enc = tok(prompts, return_tensors='pt', padding=True, add_special_tokens=False).to(device)
                with torch.inference_mode():
                    gen = model.generate(**enc, max_new_tokens=args.max_new_tokens, do_sample=False)
                for r, p, ids in zip(batch, prompts, gen[:, enc['input_ids'].shape[1]:]):
                    pred = parse_calls(ids, p)
                    gold = json.loads(r['calls'])
                    outs.append(dict(id=r['id'], split=split, category=r['category'], language=r['language'], match=scorer.calls_match(gold, pred),
                                     predicted=pred, text=tok.decode(ids, skip_special_tokens=False)[:600]))
                print(f'  {tag} {split}: {len(outs)}/{len(rows)}', flush=True)
            C.write_jsonl(args.out / f'eval-{tag}-{split}.jsonl', outs)
            by_cat = {}
            for o in outs:
                by_cat.setdefault(o['category'], []).append(o['match'])
            results[split] = dict(all=C.rate([o['match'] for o in outs]), by_category={k: C.rate(v) for k, v in sorted(by_cat.items())})
            print(tag, split, results[split]['all']['rate'], {k: round(v['rate'], 2) for k, v in results[split]['by_category'].items()}, flush=True)
        return results

    split_rows = {}
    for split in SPLITS:
        rows = [dict(r) for r in ds[split]]
        if args.n:
            rows = random.Random(args.seed).sample(rows, min(args.n, len(rows)))
        split_rows[split] = rows
    manifest: dict = dict(dataset=DATASET, dataset_revision=DATASET_REVISION, model=C.MODEL, model_revision=C.MODEL_REVISION,
                          args={k: str(v) for k, v in vars(args).items()}, eval_rows={s: len(r) for s, r in split_rows.items()},
                          runner_sha256=C.sha256_file(__file__), scorer_sha256=C.sha256_file(S.__file__), environment=C.environment(device),
                          prompt_tokens_example=len(tok(build_prompt(ds['train'][0]), add_special_tokens=False).input_ids))
    start = time.monotonic()
    model = C.load_model(device, dtype, tiny=args.tiny_test)
    manifest['attn_implementation'] = getattr(model.config, '_attn_implementation', None)
    manifest['original'] = evaluate(model, 'original', split_rows)
    manifest['parse_errors_original'] = dict(parse_errors)
    if args.eval_only:
        manifest['wall_seconds'] = time.monotonic() - start
        C.write_json(args.out / 'results.json', manifest)
        print('EVAL ONLY DONE')
        return

    # training requests: the no-call requests are shown twice
    train_rows = [dict(r) for r in ds['train']]
    train_rows += [r for r in train_rows if r['category'] in ('no_tool', 'clarify')]
    random.Random(args.seed).shuffle(train_rows)
    if args.limit_train:
        train_rows = train_rows[:args.limit_train]
    train = Dataset.from_list([dict(id=r['id'], category=r['category'], calls=r['calls'], prompt=build_prompt(r)) for r in train_rows])
    manifest['train_requests'] = len(train)
    manifest['train_categories'] = dict(Counter(r['category'] for r in train_rows))

    def tool_call_reward(prompts, completion_ids, calls, **kwargs):
        rewards = []
        for prompt, ids, gold in zip(prompts, completion_ids, calls):
            gold, pred = json.loads(gold), parse_calls(ids, prompt)
            rewards.append(1.0 if scorer.calls_match(gold, pred) else 0.2 * scorer.name_f1(gold, pred))
        return rewards

    g = args.num_generations
    cfg = GRPOConfig(output_dir=str(args.out / 'trainer'), max_steps=args.max_steps, per_device_train_batch_size=2,
                     gradient_accumulation_steps=16, num_generations=g, generation_batch_size=g,
                     max_completion_length=args.max_completion_length, temperature=1.0, learning_rate=args.lr, beta=args.beta,
                     lr_scheduler_type='constant_with_warmup', warmup_steps=min(5, args.max_steps), logging_steps=1 if args.max_steps < 20 else 5,
                     save_strategy='no', bf16=dtype == torch.bfloat16, use_cpu=device == 'cpu', seed=args.seed, data_seed=args.seed,
                     report_to='none', dataloader_num_workers=0)
    peft_config = LoraConfig(r=args.rank, lora_alpha=2 * args.rank, lora_dropout=0.0, target_modules=TARGETS, task_type='CAUSAL_LM')
    checks = []

    class FiniteGradients(TrainerCallback):
        def on_pre_optimizer_step(self, a, state, control, model=None, **k):
            grads = [p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
            assert grads and all(bool(torch.isfinite(x).all()) for x in grads), 'non-finite gradient'
            checks.append(state.global_step)

    parse_errors.clear()
    trainer = GRPOTrainer(model=model, reward_funcs=tool_call_reward, args=cfg, train_dataset=train, processing_class=tok,
                          peft_config=peft_config, callbacks=[FiniteGradients()])
    manifest['trainable_parameters'] = sum(p.numel() for p in trainer.model.parameters() if p.requires_grad)
    t0 = time.monotonic()
    result = trainer.train()
    manifest['train'] = dict(metrics=result.metrics, steps=trainer.state.global_step, finite_gradient_steps=len(checks),
                             wall_seconds=time.monotonic() - t0, log_history=trainer.state.log_history,
                             parse_errors=dict(parse_errors), peak_gpu_gb=(torch.cuda.max_memory_reserved() / 1e9 if device == 'cuda' else None))
    assert len(checks) == trainer.state.global_step, 'gradient check did not run on every step'
    manifest['learning_check'] = C.learning_check(trainer.state.log_history, 'grpo')
    print('LEARNING CHECK', json.dumps(manifest['learning_check']), flush=True)
    manifest['adapter_tensors_cast_to_fp32'] = C.adapter_to_fp32(trainer.model)
    trainer.save_model(str(args.out / 'adapter'))
    tuned = trainer.model
    parse_errors.clear()
    manifest['trained'] = evaluate(tuned, 'trained', split_rows)
    manifest['parse_errors_trained'] = dict(parse_errors)

    # original vs fine-tuned on the hand-checked showcase requests (adapter switched off for the original)
    show, parity_items = [], []
    for r in [dict(x) for x in ds['showcase']]:
        gold, p = json.loads(r['calls']), build_prompt(r)
        enc = tok([p], return_tensors='pt', add_special_tokens=False).to(device)
        row = dict(id=r['id'], language=r['language'], category=r['category'], request=r['request'], gold=gold)
        for tag, off in (('original', True), ('trained', False)):
            with (tuned.disable_adapter() if off else contextlib.nullcontext()), torch.inference_mode():
                out = tuned.generate(**enc, max_new_tokens=args.max_new_tokens, do_sample=False)[0, enc['input_ids'].shape[1]:]
            pred = parse_calls(out, p)
            row[tag] = dict(calls=pred, match=scorer.calls_match(gold, pred), text=tok.decode(out, skip_special_tokens=False)[:400])
            if tag == 'trained' and len(parity_items) < 4 and len(out):
                parity_items.append((enc['input_ids'][0], out))
        show.append(row)
    C.write_json(args.out / 'showcase.json', show)

    # reload parity on the trained model's own answers: noise (trained vs reloaded) must be small against the effect (adapter on vs off)
    on = C.generated_logprobs(tuned, parity_items, device)
    with tuned.disable_adapter():
        off = C.generated_logprobs(tuned, parity_items, device)
    del trainer, tuned, model
    gc.collect()
    if device == 'cuda':
        torch.cuda.empty_cache()
    reloaded = PeftModel.from_pretrained(C.load_model(device, dtype, tiny=args.tiny_test), str(args.out / 'adapter')).eval() if not args.tiny_test else None
    if reloaded is not None:
        manifest['reload_parity'] = C.reload_parity(on, off, C.generated_logprobs(reloaded, parity_items, device))
    manifest['adapter_files'] = {p.name: C.sha256_file(p) for p in (args.out / 'adapter').iterdir() if p.is_file()}
    manifest['wall_seconds'] = time.monotonic() - start
    C.write_json(args.out / 'results.json', manifest)
    print('PASSED')


if __name__ == '__main__':
    main()
