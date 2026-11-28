"""preference-rl exp-003: DPO on the Turkish repair pairs plus the skill-preserving pairs (training only; evaluation runs separately).

Recipe = the Liquid notebook as in run_pref_dpo_grounded_qa.py: LoRA r16/alpha32/dropout .05 on attention, conv and MLP projections,
loss sigmoid-DPO + SFT on the chosen answers (1, 1), beta .1, LR 2e-5 cosine, warmup 10%, batch 2 x 8, max length 3072, 1 epoch.
Two arms on the same pairs: --arm sft (start from the published exp-021 weights in --sft-dir) and --arm base (the original LFM3-1.7B).
The pairs file is the mix from tr_dpo_skill_pairs.py (prompt, chosen, rejected, chat_template_kwargs, optional tools, lane). Thinking
inside assistant messages and tools go through TRL's own chat-template calls.
  python scripts/training/run_tr_dpo_train.py --pairs PAIRS --arm sft --sft-dir DIR --out DIR                  # the run
  python scripts/training/run_tr_dpo_train.py --pairs PAIRS --arm base --out DIR --limit-train 32 --epochs 10 --lr 1e-4   # tiny-overfit check
Smoke test on CPU: add --tiny-test --device cpu --limit-train 8 --max-length 512.
After training: the adapter, a merged 16-bit model (for the evaluation stack), per-lane DPO metrics before and after, results.json.
"""
import argparse
import collections
import gc
import json
import time
from pathlib import Path

import pref_rl_common as C

TARGETS = ['q_proj', 'k_proj', 'v_proj', 'o_proj', 'in_proj', 'out_proj', 'w1', 'w2', 'w3']
KEEP = ('prompt', 'chosen', 'rejected', 'chat_template_kwargs', 'tools', 'lane')


def load_pairs(path, limit):
    rows = [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
    ids = [r['id'] for r in rows]
    assert len(ids) == len(set(ids)), 'duplicate pair ids'
    if limit:  # alternate lanes so a small smoke set still has both
        by = collections.defaultdict(list)
        for r in rows:
            by[r['lane']].append(r)
        rows = [r for pair in zip(*by.values()) for r in pair][:limit]
    for r in rows:
        assert set(('prompt', 'chosen', 'rejected', 'chat_template_kwargs', 'lane')) <= set(r), r['id']
        assert r['prompt'][-1]['role'] == 'user' and r['chosen'][0]['role'] == 'assistant' and r['rejected'][0]['role'] == 'assistant', r['id']
    return rows


def trainer_row(r):
    out = {k: r[k] for k in KEEP if k in r and r[k] is not None}
    out['tools'] = json.dumps(r['tools'], ensure_ascii=False) if r.get('tools') else None
    return out


def render(tok, r, answer_key):
    kw = dict(tools=r.get('tools'), **r['chat_template_kwargs'])
    return tok.apply_chat_template(r['prompt'] + r[answer_key], tokenize=True, return_dict=True, **kw)['input_ids']


def length_report(tok, rows, max_length):
    """Token counts of prompt plus the longer answer; pairs over max_length would be cut by TRL (per lane)."""
    over, longest = collections.Counter(), collections.Counter()
    for r in rows:
        n = max(len(render(tok, r, 'chosen')), len(render(tok, r, 'rejected')))
        longest[r['lane']] = max(longest[r['lane']], n)
        over[r['lane']] += n > max_length
    return dict(over_max_length=dict(over), longest=dict(longest))


def check_tokenization(tok, trainer, rows):
    """TRL's tokenisation of the stored dataset must equal a direct chat-template rendering (guards against tools, thinking or
    kwargs being dropped by the dataset round trip)."""
    ds = trainer.train_dataset
    bad = []
    for i, r in enumerate(rows):
        row = ds[i]
        for key, ids in (('chosen', row['chosen_ids']), ('rejected', row['rejected_ids'])):
            want = render(tok, r, key)
            got = list(row['prompt_ids']) + list(ids)
            if got != want[:len(got)] or len(got) < min(len(want), trainer.args.max_length or len(want)):
                bad.append((r['id'], key))
    assert not bad, f'TRL tokenisation differs from the direct rendering for {len(bad)} sides, first: {bad[:3]}'
    return len(rows)


def load_arm_model(args, device, dtype):
    from transformers import AutoModelForCausalLM
    if args.tiny_test:
        return C.load_model(device, dtype, tiny=True)
    if args.arm == 'base':
        return C.load_model(device, dtype)
    assert args.sft_dir and (args.sft_dir / 'model.safetensors').exists(), 'dpo-on-sft arm needs --sft-dir with the exp-021 weights'
    return AutoModelForCausalLM.from_pretrained(str(args.sft_dir), trust_remote_code=True, dtype=dtype).to(device)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pairs', type=Path, required=True)
    ap.add_argument('--arm', choices=('sft', 'base'), required=True)
    ap.add_argument('--sft-dir', type=Path, default=None, help='local copy of the exp-021 weights (arm sft)')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--device', default='auto')
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--lr', type=float, default=2e-5)
    ap.add_argument('--beta', type=float, default=0.1)
    ap.add_argument('--rank', type=int, default=16)
    ap.add_argument('--epochs', type=float, default=1.0)
    ap.add_argument('--max-length', type=int, default=3072)
    ap.add_argument('--limit-train', type=int, default=0, help='Smoke test or overfit check: first N pairs, alternating lanes')
    ap.add_argument('--sft-weight', type=float, default=1.0)
    ap.add_argument('--dpo-weight', type=float, default=1.0, help='0 gives the SFT-only control arm (same chosen answers, no preference term)')
    ap.add_argument('--no-merge', action='store_true')
    ap.add_argument('--no-lane-metrics', action='store_true', help='skip the per-lane before/after metrics (a dev sweep does not need them)')
    ap.add_argument('--tiny-test', action='store_true', help='Pipeline test with a random miniature model (no real results)')
    args = ap.parse_args()
    C.check_pins()
    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import TrainerCallback, set_seed
    from trl import DPOConfig, DPOTrainer

    assert not args.out.exists(), 'Preserve the existing attempt'
    args.out.mkdir(parents=True)
    device, dtype = C.pick_device(args.device)
    set_seed(args.seed)
    tok = C.load_tokenizer()
    if args.arm == 'sft' and not args.tiny_test:  # the published SFT model must use the template of the original model
        from transformers import AutoTokenizer
        sft_tok = AutoTokenizer.from_pretrained(str(args.sft_dir), trust_remote_code=True)
        assert sft_tok.chat_template == tok.chat_template, 'exp-021 chat template differs from the original'
    rows = load_pairs(args.pairs, args.limit_train)
    manifest: dict = dict(pairs_file=str(args.pairs), pairs_sha256=C.sha256_file(args.pairs), arm=args.arm, args={k: str(v) for k, v in vars(args).items()},
                          model=C.MODEL, model_revision=C.MODEL_REVISION, runner_sha256=C.sha256_file(__file__), environment=C.environment(device),
                          train_pairs=len(rows), lanes=dict(collections.Counter(r['lane'] for r in rows)),
                          thinking_pairs=sum(r['chat_template_kwargs'].get('enable_thinking', False) for r in rows), tool_pairs=sum(bool(r.get('tools')) for r in rows),
                          rejected_cut_off=sum(r.get('rejected_finished') is False for r in rows))
    if args.arm == 'sft' and not args.tiny_test:
        manifest['sft_weights_sha256'] = C.sha256_file(args.sft_dir / 'model.safetensors')
    manifest['lengths'] = length_report(tok, rows, args.max_length)
    print('PAIRS', json.dumps({k: manifest[k] for k in ('train_pairs', 'lanes', 'thinking_pairs', 'tool_pairs', 'rejected_cut_off', 'lengths')}), flush=True)
    start = time.monotonic()
    model = load_arm_model(args, device, dtype)
    manifest['attn_implementation'] = getattr(model.config, '_attn_implementation', None)
    lanes = sorted({r['lane'] for r in rows})
    data = Dataset.from_list([trainer_row(r) for r in rows])
    evals = {lane: Dataset.from_list([trainer_row(r) for r in rows if r['lane'] == lane]) for lane in lanes}
    cfg = DPOConfig(output_dir=str(args.out / 'trainer'), num_train_epochs=args.epochs, per_device_train_batch_size=2, per_device_eval_batch_size=2,
                    gradient_accumulation_steps=8, learning_rate=args.lr, loss_type=['sigmoid', 'sft'], loss_weights=[args.dpo_weight, args.sft_weight],
                    lr_scheduler_type='cosine', warmup_steps=0.1, beta=args.beta, max_length=args.max_length, logging_steps=5,
                    save_strategy='no', eval_strategy='no', bf16=dtype == torch.bfloat16, use_cpu=device == 'cpu', seed=args.seed,
                    data_seed=args.seed, report_to='none', dataloader_num_workers=0)
    peft_config = LoraConfig(r=args.rank, lora_alpha=2 * args.rank, lora_dropout=0.05, target_modules=TARGETS, task_type='CAUSAL_LM')
    checks = []

    class FiniteGradients(TrainerCallback):
        def on_pre_optimizer_step(self, a, state, control, model=None, **k):
            grads = [p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
            assert grads and all(bool(torch.isfinite(g).all()) for g in grads), 'non-finite gradient'
            checks.append(state.global_step)

    trainer = DPOTrainer(model=model, args=cfg, train_dataset=data, eval_dataset=evals, processing_class=tok, peft_config=peft_config,
                         callbacks=[FiniteGradients()])
    manifest['tokenization_checked_rows'] = check_tokenization(tok, trainer, rows)
    manifest['trainable_parameters'] = sum(p.numel() for p in trainer.model.parameters() if p.requires_grad)

    def lane_metrics(tag):
        """Per lane over the training pairs: DPO reward margin and accuracy (policy against the same model with the adapter off), mean log-probability
        of the chosen and of the rejected answers, and the eval loss. TRL's evaluate() logs only the loss, so the margins are computed here."""
        m = trainer.evaluate()  # the eval dataset dict given at init: one metric prefix per lane
        policy = trainer.model.eval()
        got = {lane: dict(margin=[], chosen=[], rejected=[], chosen_gain=[]) for lane in lanes}

        def logp(row, key, reference):
            ids = torch.tensor([(list(row['prompt_ids']) + list(row[key]))[:args.max_length]], device=device)
            start = len(row['prompt_ids'])
            with torch.no_grad():
                if reference:
                    with policy.disable_adapter():
                        logits = policy(input_ids=ids).logits[0, :-1].float()
                else:
                    logits = policy(input_ids=ids).logits[0, :-1].float()
            lps = torch.log_softmax(logits, -1).gather(1, ids[0, 1:, None])[:, 0]
            return lps[start - 1:].sum().item()

        for i, r in enumerate(rows):
            row = trainer.train_dataset[i]
            pc, pr = logp(row, 'chosen_ids', False), logp(row, 'rejected_ids', False)
            rc, rr = logp(row, 'chosen_ids', True), logp(row, 'rejected_ids', True)
            g = got[r['lane']]
            g['margin'].append(args.beta * ((pc - rc) - (pr - rr)))
            g['chosen'].append(pc)
            g['rejected'].append(pr)
            g['chosen_gain'].append(pc - rc)
        out = {}
        for lane in lanes:
            g = got[lane]
            out[lane] = dict(pairs=len(g['margin']), margin=sum(g['margin']) / len(g['margin']), accuracy=sum(x > 0 for x in g['margin']) / len(g['margin']),
                             chosen_logp=sum(g['chosen']) / len(g['chosen']), rejected_logp=sum(g['rejected']) / len(g['rejected']),
                             chosen_logp_gain=sum(g['chosen_gain']) / len(g['chosen_gain']), eval_loss=m[f'eval_{lane}_loss'])
        print('LANE METRICS', tag, json.dumps({lane: {k: round(v, 4) for k, v in x.items()} for lane, x in out.items()}), flush=True)
        policy.train()
        return out

    manifest['lane_metrics_before'] = None if args.no_lane_metrics else lane_metrics('before')
    t0 = time.monotonic()
    result = trainer.train()
    manifest['train'] = dict(metrics=result.metrics, steps=trainer.state.global_step, finite_gradient_steps=len(checks), wall_seconds=time.monotonic() - t0,
                             log_history=trainer.state.log_history, peak_gpu_gb=(torch.cuda.max_memory_reserved() / 1e9 if device == 'cuda' else None))
    assert len(checks) == trainer.state.global_step, 'gradient check did not run on every step'
    manifest['learning_check'] = C.learning_check(trainer.state.log_history, 'dpo')
    print('LEARNING CHECK', json.dumps(manifest['learning_check']), flush=True)
    manifest['lane_metrics_after'] = None if args.no_lane_metrics else lane_metrics('after')
    trainer.save_model(str(args.out / 'adapter'))
    manifest['adapter_files'] = {p.name: C.sha256_file(p) for p in (args.out / 'adapter').iterdir() if p.is_file()}
    if not args.no_merge and not args.tiny_test:
        merged = trainer.model.merge_and_unload()
        merged.save_pretrained(str(args.out / 'merged'), safe_serialization=True)
        tok.save_pretrained(str(args.out / 'merged'))
        manifest['merged_sha256'] = C.sha256_file(args.out / 'merged' / 'model.safetensors')
    del trainer, model
    gc.collect()
    manifest['wall_seconds'] = time.monotonic() - start
    C.write_json(args.out / 'results.json', manifest)
    print('PASSED')


if __name__ == '__main__':
    main()
