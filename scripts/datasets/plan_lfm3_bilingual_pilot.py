"""Deterministic data order + supervised-token budget matching for the two bilingual-pilot arms (planning only).

Arm A: Turkish-only (tr-tr rows, 160), 5 epochs = 100 optimizer steps at batch 8 (the exp-007 recipe).
Arm B: four-direction bilingual (640 rows). Same recipe; the number of optimizer steps is chosen so that cumulative
SUPERVISED tokens match arm A's total (not the epoch count). Both arms use an explicit per-epoch permutation
(random.Random(seed + epoch)) so token exposure is known exactly before any run and is reproducible.

  python scripts/datasets/plan_lfm3_bilingual_pilot.py
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bilingual_pilot_common import PILOT, freeze, json_bytes, read_jsonl, sha256_file

SEED = 3407  # same seed/data_seed as exp-007
BATCH = 8    # micro_batch 2 x grad accumulation 4, one GPU
OUT = PILOT / 'plan'


def order(n_rows, n_epochs_needed, seed=SEED):
    seq = []
    for epoch in range(n_epochs_needed):
        perm = list(range(n_rows))
        random.Random(seed + epoch).shuffle(perm)
        seq.extend(perm)
    return seq


def cumulative(seq, tokens):
    total, out = 0, []
    for step in range(len(seq) // BATCH):
        total += sum(tokens[i] for i in seq[step * BATCH:(step + 1) * BATCH])
        out.append(total)
    return out


def main():
    rows = read_jsonl(PILOT / 'data/train.jsonl')
    tok = {r['id']: r for r in read_jsonl(PILOT / 'validation/row-token-lengths.jsonl')}
    a_rows = [r for r in rows if r['direction'] == 'tr-tr']
    b_rows = rows
    a_sup = [tok[r['id']]['supervised'] for r in a_rows]
    b_sup = [tok[r['id']]['supervised'] for r in b_rows]
    a_masked = [tok[r['id']]['masked'] for r in a_rows]
    b_masked = [tok[r['id']]['masked'] for r in b_rows]
    a_steps = 100
    a_seq = order(len(a_rows), 5)
    a_cum = cumulative(a_seq, a_sup)
    a_total = a_cum[-1]
    assert a_total == 5 * sum(a_sup) and len(a_seq) == 800
    b_seq = order(len(b_rows), 3)  # 3 epochs is more than enough rows for the search window
    b_cum = cumulative(b_seq, b_sup)
    window = range(100, 131)
    candidates = [dict(steps=s, rows=s * BATCH, epochs=round(s * BATCH / 640, 3), supervised_tokens=b_cum[s - 1],
                       relative_to_arm_a=round(b_cum[s - 1] / a_total - 1, 5)) for s in window]
    best = min(candidates, key=lambda c: (abs(c['relative_to_arm_a']), c['steps']))
    b_steps = best['steps']
    # checkpoint at the step whose cumulative supervised tokens are closest to 60% of each arm's own budget (A: step 60 = epoch 3).
    a_60 = min(range(1, a_steps + 1), key=lambda s: abs(a_cum[s - 1] / a_total - 0.6))
    b_60 = min(range(1, b_steps + 1), key=lambda s: abs(b_cum[s - 1] / b_cum[b_steps - 1] - 0.6))
    a_masked_total = sum(a_masked[i] for i in a_seq)
    b_masked_total = sum(b_masked[i] for i in b_seq[:b_steps * BATCH])
    plan = dict(
        status='planning-artifact; no training executed',
        seed=SEED, batch_rows_per_step=BATCH, order_mechanism='epoch e permutation = random.Random(seed+e).shuffle(range(n_rows)); rows consumed sequentially, no packing, no dropped last batch (all totals are multiples of 8)',
        python_version=sys.version.split()[0],
        arm_a=dict(rows=len(a_rows), source='data/train-arm-a-tr-only.jsonl', epochs=5, optimizer_steps=a_steps,
                   supervised_tokens_per_epoch=sum(a_sup), supervised_tokens_total=a_total, masked_context_tokens_total=a_masked_total,
                   mean_supervised_tokens_per_row=round(sum(a_sup) / len(a_sup), 2), checkpoint_steps=[a_60, a_steps],
                   checkpoint_note='step 60 = epoch 3 (identical to exp-007)'),
        arm_b=dict(rows=len(b_rows), source='data/train.jsonl', optimizer_steps=b_steps, rows_consumed=b_steps * BATCH,
                   epochs_equivalent=round(b_steps * BATCH / 640, 3), supervised_tokens_per_epoch=sum(b_sup),
                   supervised_tokens_total=b_cum[b_steps - 1], supervised_vs_arm_a=best['relative_to_arm_a'],
                   masked_context_tokens_total=b_masked_total, mean_supervised_tokens_per_row=round(sum(b_sup) / len(b_sup), 2),
                   checkpoint_steps=[b_60, b_steps],
                   checkpoint_note='steps closest to 60% and 100% of the arm-B supervised-token budget (matches A step60/100 by exposure fraction)'),
        search_window=candidates,
        unavoidable_differences=[
            'optimizer update count: A=100 vs B=%d (token matching with 8 rows/step; B rows are shorter on average)' % b_steps,
            'epochs: A=5 vs B=%.2f; unique rows 160 vs 640; per-task exposure is 5 (same text) vs %.1f (four direction variants)' % (b_steps * BATCH / 640, b_steps * BATCH / 160),
            'cosine horizon scales with the update count (6 warmup steps kept identical)',
            'masked context tokens differ (%d vs %d) because EN prompts and EN-system prompts are included in B' % (a_masked_total, b_masked_total),
            'half of B targets are English, which the LFM3 tokenizer encodes in ~24% fewer tokens than the Turkish targets, so an equal supervised-token budget consumes more rows'],
        order_a=a_seq, order_b=b_seq[:b_steps * BATCH],
        inputs={'data/train.jsonl': sha256_file(PILOT / 'data/train.jsonl'), 'validation/row-token-lengths.jsonl': sha256_file(PILOT / 'validation/row-token-lengths.jsonl')})
    OUT.mkdir(parents=True, exist_ok=True)
    freeze(OUT / 'token-budget-and-order.json', json_bytes(plan))
    print(json.dumps({k: plan[k] for k in ('arm_a', 'arm_b')}, indent=1))


if __name__ == '__main__':
    main()
