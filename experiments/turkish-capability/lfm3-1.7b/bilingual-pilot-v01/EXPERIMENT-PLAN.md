# Experiment plan: Turkish-only vs four-direction bilingual SFT (prepared, NOT executed)

Active dataset: `revisions/v01-corrections-02/` (`ACTIVE-REVISION.json`). Both arms use the same owner-authorized repairs. Configs and the revision token plan are authoritative. No training started.


Experiments: `exp-010-tr-only-sft160` (A) and `exp-011-bilingual-sft640` (B). Parent recipe: exp-007-sft160-lr1e4 (current research candidate, best of the pilot160 pair; config read from `exp-007.../config.yaml`, not guessed).

## Hypothesis
Aligned bilingual task-solving supervision (same 160 tasks in TR/EN input x TR/EN output) transfers existing English skill to Turkish input, improves output-language control and Turkish meaning, without worsening arithmetic, English, stopping or formatting. Not established by any prior result.

## Identical in both arms (copied from exp-007)
Fresh LoRA on the same pinned CPT merge (CPT@6f213ec2 over LFM3-1.7B@0dc4268b); r32/alpha64/dropout 0, 9 modules, embeddings frozen; LR 1e-4 cosine, 6 warmup steps, AdamW fused, wd 0, clip 1.0; micro-batch 2 x accumulation 4 (batch 8), BF16, max_length 4096, no packing, gradient checkpointing; seed/data_seed 3407; assistant-only loss incl. `<think></think>` and end-of-turn 124900; 130 direct-answer rows keep blank thinking, 30 reasoning rows keep reasoning separate; no LR/rank sweep.

## Intended differences
| | A | B |
|---|---|---|
| Rows | 160 (`tr-tr`, with "Yanıtını Türkçe ver.") | 640 (4 directions) |
| Optimizer steps | 100 (5 epochs) | 113 (1.4125 epochs) |
| Supervised tokens | 208,665 | 209,811 (+0.55%) |
| Checkpoints | 60 (=epoch 3), 100 | 69, 113 (nearest A checkpoint token exposures) |

Token matching: supervised tokens per epoch are 46,088 (A) vs 162,196 (B; English targets are ~24% shorter). Both arms use an explicit per-epoch permutation (`plan/token-budget-and-order.json`), so exposure is exact and known before running (needs a runner that consumes the order file; `run_lfm3_sft160.py` hard-codes 100 steps and the pilot160 data).

## Unavoidable differences (documented)
Update count (100 vs 113) and cosine horizon; epochs 5 vs 1.4125; masked context exposure differs (recompute from revision lengths and order); B includes an English system prompt and English prompts; 18 EN-output rows are language-bound (see decisions #4). Single seed: exploratory only; repeat before any claim.

## Checkpoint selection (frozen before results)
Per arm choose between its two checkpoints using development data only: dev20, crosslingual-holdout-v01 (12+3), CETVEL100 + TurBLiMP1600; earlier checkpoint on practical ties. The new `eval-v01` (35x4 + 8 symbolic) is scored once afterwards and never used for selection. Old20/dev20/xling stay development/regression, not a final test.

## Evaluation and regressions (same frozen inference as historical runs)
vLLM BF16/eager/batch 4, ctx 8192, max 4096 new tokens, T 0.1, top-k 50, top-p 1, rp 1.1, seed 3407, thinking disabled, explicit EOT + loop guard; raw outputs/token IDs/finish reasons saved. Report per direction and per category, never pooled: Turkish understanding (TR->TR, TR->EN vs EN->EN), output-language compliance (EN->TR, TR->EN), arithmetic (8 tasks + 8 symbolic controls + old 3), negation, semantic roles, faithful rewriting, English retention (EN->EN), stopping (EOS/loop/cap counts), formatting (numeric-only, bullet counts, JSON). References live only in `eval-v01/*references*.jsonl`; keep them out of annotation displays and model input. Baselines: untouched LFM3-1.7B and CPT-merged parent; optionally exp-007 step 60.

## Pre-run gates (all still open)
Owner answers decisions #1-#4; re-run `validate_lfm3_bilingual_pilot.py` and the eval freeze check; native rendered/tokenized/label audit incl. `</think>` leakage; finite-loss smoke, save/reload parity, train-only tiny overfit; record environment/hardware per `docs/reproducibility.md`; clean-tree commit hash for builders (nothing is committed yet).

## Success criteria (freeze before training)
B improves Turkish-input cases and output-language compliance over A without losing previously correct English/symbolic cases or adding stopping regressions. With 35 correlated tasks, a one-case change is inspection evidence, not a gain.
