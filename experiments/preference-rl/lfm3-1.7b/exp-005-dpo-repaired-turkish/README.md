# exp-005 DPO on repaired Turkish answers (data-carrying prompts, minimal repair, SFT-only control)

## Status

`ready` (2026-11-26). Prompt pool, held-out set, repair packets, repair guide and validator exist; no answer has been repaired yet. The rules below
are fixed before any repaired data or model result exists.

## Goal

Find out whether DPO with the notebook's recipe improves the content and format quality of the Turkish SFT model's answers on tasks that carry their
own data (summarise, extract, list under limits), and whether the preference term adds anything beyond SFT on the same repaired answers.

## Hypothesis

Pairs where rejected is exp-021's own answer and chosen is the same answer with only its errors fixed (contradicted or invented claims, broken limits,
invented words, broken grammar) teach the model to stay with the given data, meet the stated limits and write clean Turkish. A blind comparison on
unseen data-carrying prompts prefers the trained model over exp-021.

## Parent Experiment

`exp-003-dpo-turkish-quality` (null result: 131 Turkish pairs, 14 steps) and `exp-004-dpo-onpolicy-turkish` (not trained: 27 of 30 audited
"clean" chosen answers were wrong at task level). Control: `exp-001-dpo-grounded-qa` (the notebook's data, 4,072 pairs, clear gain).

## What Changed

| | exp-003 | exp-004 | exp-005 |
|---|---|---|---|
| Prompts | 526 open and data-carrying | 3,948 | 2,000 train + 200 held-out, **only prompts that carry data** (open knowledge or advice questions excluded: DPO cannot teach facts) |
| rejected | flagged sample, mildest | flagged sample | one random finished exp-021 sample, no detector selection |
| chosen | edited by hand-supervised model, 36% usable | detector-clean sample | **repaired by a strong model**, validated by code, 3 verdicts, rewrites dropped |
| Length | band 0.85-1.15 | band 0.85-1.15 | chosen/rejected words 0.70-1.10 (mild brevity is wanted; the floor stops the exp-016 brevity bias) |
| Judging of the result | detector flagged share | detector flagged share | **blind pairwise comparison of content**, detectors only as side checks |
| Arms | dpo-on-sft, dpo-on-base | same | **dpo-on-sft and sft-only** (same chosen answers, DPO weight 0) |
| Steps | 14 | about 220 | 3 epochs, about 200 steps |

Unchanged: recipe (sigmoid + SFT loss, beta 0.1, LR 2e-5 cosine, warmup 10%, LoRA r16/alpha 32, batch 2 x 8, max length 3,072), model (exp-021),
detectors. The sample pool is exp-004's 8 samples per prompt (same sampler).

## Base Model

`cbarkinozer/LFM3-1.7B-Turkish-SFT` (exp-021, pinned commit `6e4f0b7658b115a28da971f82ff4009f63bed612`), bfloat16, thinking off. Reference model: the
same model with the adapter off.

## Dataset

Source: exp-004's `data/prompts-tr-dpo4.jsonl` (Atlas-based, MIT, excludes the SFT core prompts) and its 31,584 samples. Groups: `constraint` (Atlas
prompts with countable limits), `context`, `plain_source` (plain prompts with at least 15 words after the first line break). Held-out: 200 prompts cut
first (131 / 61 / 8) and never repaired or trained on. Train: 2,000 prompts (1,300 / 118 / 582). One finished sample per prompt, chosen by hash rank, is
repaired; the manifest `data/repair-pool-manifest.json` has the ids, the sample numbers and the input hashes.

Repair: `data/REPAIR-GUIDE.md` (rules, verdicts, two worked examples from the owner-reviewed fixes). Check: `scripts/datasets/tr_dpo_repair.py validate`
(detectors with the accept list, constraint checker with a normalisation for decimal numbers and `1-` list markers, word range 0.70-1.10, ending, `none`
and `rewrite_needed` dropped). Failed repairs get one retry with the failure reasons, then are dropped. Pairs are labelled `synthetic_repair`; the
packets and pairs stay local (not in Git).

Why there is no minimal-edit similarity gate: the 17 repairs made during the exp-004 audit (by a strong model, read and judged legitimate in a second
pass) had a median character similarity of 0.40 to the original chosen answer (some started from the rejected answer instead), so a 50% gate would
have discarded most good repairs. The similarity is recorded and reported per verdict, and `larger` pairs are over-sampled in the owner's reads.

## Training Setup

LoRA DPO + SFT (`scripts/training/run_tr_dpo_train.py`), seed 42, 3 epochs (about 200 steps for 1,000-1,300 pairs; the notebook ran 255 steps), arms:
`dpo-on-sft` (default) and `sft-only` (`--dpo-weight 0`, same chosen answers). Pod launch through the session script's `variant` stage. At least 1,000
usable pairs are needed; if fewer, a second sample per prompt (`alt_sample`) is repaired.

## Evaluation

Held-out answers from exp-021, `dpo-on-sft` and `sft-only`, same decoding (temperature 0.1, top_k 50, repetition penalty 1.1, max 800 new tokens,
thinking off, one answer per prompt; a temperature-0.7 second answer is a reported sensitivity check). Judge: a model of a different family than the
repair model, blind and order-randomised, instructions fixed in `data/JUDGE-GUIDE.md` before any answer exists, ties allowed. Secondary set: exp-003's
78 held-out open prompts (expect no change). Guards: IFEval strict on and off, HumanEval, final-test math EN and TR, Belebele EN and TR (source file
on the pod fixed first), TurBLiMP, tool calls.

## Decision rules (fixed now)

Data gate (before any training): at least 50% of the 300 pilot items give a usable pair after one retry, and of 30 random pilot pairs read by the owner
(`larger` over-sampled) at least 27 have a chosen answer that is correct and better than the rejected one. Failing the gate means the repair guide is
fixed, not the gate.

1. **Target:** `dpo-on-sft` beats exp-021 in at least 60% of the decisive blind comparisons on the 200 held-out prompts and the Wilson 95% lower bound
   is above 50%.
2. **Attribution:** `dpo-on-sft` also beats `sft-only` the same way (at least 60%, lower bound above 50%). If only rule 1 passes the finding is "SFT
   on repaired answers helps; the preference term is not shown to add".
3. **Side checks** (code-checked, held-out): constraint pass rate not below exp-021's; mean words within 0.80-1.10 of exp-021's; at least 90% of answers
   end properly; detector flagged share not higher.
4. **Training integrity:** the logged `logps/chosen` at the end is not below its first logged value (DPO with near-identical pairs can push both
   answers down; the SFT term is there to prevent that).
5. **Guards:** IFEval and HumanEval within the noise of exp-021; Belebele and TurBLiMP not down by more than 1 point.
6. **Owner:** a blind read of 30 held-out comparisons prefers `dpo-on-sft` in more of the decisive ones than exp-021. One seed: a pass gets a second
   seed before any public claim.

What this will not fix: knowledge errors (wrong facts in open questions). Those need more data or a bigger model.

## Results

Not run yet.

## Regressions

Not run yet.

## Conclusion

Pending.

## Next Step

Pilot repair of 300 items (`results-local/repair-input-pilot.jsonl`), validation, owner read of 30 pairs.
