# exp-021 / exp-019 seed 2 / exp-022: reviewed Turkish rows and email rows, with controls, 2026-11-23

## Status

`completed`, exp-021 `selected` and released (2026-11-23). Design frozen 2026-11-23 10:30 UTC, before any result of these runs existed; results follow below.

## Questions

1. Does replacing the flawed free-form Turkish rows (Atlas) of the exp-019 pack by AI-reviewed rows, and adding 80 AI-written
   correspondence rows, improve Turkish writing without losing skills? (exp-021)
2. How much do results move between two identical trainings with different seeds? (exp-019 seed 2)
3. Do the 422 Atlas rows help or hurt at all? (exp-022, ablation: exp-019 pack without Atlas, nothing added)

## Runs (all on the CPT-merged parent, LoRA r32/alpha64, LR 1e-4, one epoch, max length 8192, same evaluation as exp-019)

| Run | Pack | Rows | Seed |
|---|---|---|---|
| exp-021 | exp-019 pack minus 422 Atlas rows, plus 57 reviewed Atlas rows (1 kept, 56 with the reviewer's complete corrected answer and, for 33, a corrected prompt; 3 dropped) and 80 correspondence rows, all of these trained with thinking off | 2,624 | 3407 |
| exp-019 seed 2 (`exp019s2`) | the exp-019 pack, unchanged | 2,909 | 4242 |
| exp-022 | exp-019 pack minus its 422 Atlas rows | 2,487 | 3407 |

Packs are built by `scripts/datasets/build_lfm3_sft_pack_v2.py` (report: `sft-core-v01/pack-v2-report.json`; sha256 of the packs
start `30d0c7852025b7a9` for exp-021 and `0e1d4a895c87163b` for exp-022). The corrected Atlas answers and the correspondence rows
are AI-written, not human-reviewed; the owner approved their use. The corrected rows pass the countable-constraint checker. Math,
code, tool and English replay rows are still the model's own verified answers (about 95% of the pack).

## Pre-registered rules (exp-021 against exp-019 seed 3407, base and the seed-2 spread)

Release candidate: exp-021 replaces exp-019 only if ALL hold, otherwise exp-019 stays the candidate.
- Skills (thinking on, against the base): eval v2 English math, tool calls EN and TR within 5 points; HumanEval and IFEval strict
  (270) within 5 points; final test English and Turkish within 3 points.
- Instruction following without thinking: IFEval strict on all 541 prompts not more than 3 points below exp-019; eval v2 and HumanEval
  thinking-off cells not more than 5 points below exp-019.
- Turkish reading and grammar: diagnostic cell D, Belebele Turkish (restricted) and TurBLiMP each not more than 3 points below exp-019
  and TurBLiMP at least .85.
- Writing probe with thinking on: at most 1 of 40 answers fully in English, and the AI-rated mean naturalness not below exp-019's.
- Differences smaller than the spread between exp-019 seed 3407 and seed 4242 are not claimed as gains.
exp-022 is descriptive (no gate). The thinking-off writing probe, the owner's blind preference check and the AI ratings are reported
with the same limits as exp-019 (AI ratings are not human review).

## Limits

One seed per recipe except exp-019 (two). The development sets (152 diagnostic items, Belebele) have steered earlier decisions; the
100-item final test is the cleaner check and resolves about 8 to 10 points. The email rows are AI-written and cover one style.

## Results

All values are percentages unless noted; the base is the original `LiquidAI/LFM3-1.7B`. Sources: the gate analysis
(`results-local/gates-exp021.json`, not committed) and the published model card.

### Outcome

exp-021 passed every pre-registered rule and replaced exp-019 as the release candidate. It was published as
[`cbarkinozer/LFM3-1.7B-Turkish-SFT`](https://huggingface.co/cbarkinozer/LFM3-1.7B-Turkish-SFT) (weights, Q4_K_M and Q8_0 GGUF, SFT adapter,
LICENSE copy) with the training set and a held-out test split as
[`cbarkinozer/LFM3-1.7B-Turkish-SFT-Dataset`](https://huggingface.co/datasets/cbarkinozer/LFM3-1.7B-Turkish-SFT-Dataset). The merge done on a CPU is
byte-identical to the one done on the pod's GPU.

### Rule by rule (exp-021 against the base unless noted)

| Rule | Measure | Base | exp-021 | Verdict |
|---|---|---|---|---|
| Turkish reading, diagnostic cell D (152 items x 4 seeds) | accuracy; must be at least base - 3 and above the exp-016 arm B model | 69.1 | 76.6 (+7.6, interval 3.3 to 12.0) | pass |
| Belebele Turkish, restricted | at least 45 and not more than 3 below arm B (48.3) | 35.2 | 48.7 | pass |
| TurBLiMP macro accuracy | at least 85 | 71.8 | 85.9 | pass |
| Writing probe, thinking on | at most 1 of 40 answers fully in English | n/a | 0 of 40 (2 answers without an end token) | pass |
| IFEval strict, thinking on (270) | within 5 of the base | 84.1 | 84.4 | pass |
| HumanEval, thinking on (164) | within 5 of the base | 92.7 | 92.7 | pass |
| Skills (tool calls, English math, final test) | within 5 (3 for the final test) of the base, from the eval v2 comparison logs | | tool calls EN 95.0 to 91.3, TR 82.5 to 87.5; final test EN 93.8 to 92.7, TR 76.3 to 78.2 | pass |

Reported without a gate: IFEval strict without thinking on all 541 prompts 73.0 to 69.9 (difference -3.1, interval -7.0 to +0.6, the
gate against exp-019 passed); HumanEval without thinking 76.2 to 73.2 (difference -3.0, interval -10.4 to +3.7, ambiguous).

### What each stage did

| Stage | TurBLiMP | Belebele TR | Belebele EN |
|---|---|---|---|
| original | 71.8 | 35.2 | 67.0 |
| + Turkish CPT (100M tokens) | 86.8 | 26.4 | 60.4 (only 136 of 500 test generations ended normally) |
| + self-distillation SFT (exp-021) | 85.9 | 48.7 | 70.0 |

CPT gives the grammar and breaks reading and chat behaviour; the SFT repairs the second without losing the first.

### Controls

- **SFT without the CPT parent** (exp-020, same data as exp-019 on the original base): TurBLiMP 71.9, Belebele TR 41.4, cell D 71.1. The grammar gain
  is the CPT's; the SFT alone gives part of the reading gain.
- **exp-019 seed 2** (identical recipe, seed 4242): within the seed noise of exp-021. Two seeds of the same recipe differed by up to
  7 points on Turkish math, so differences of a few points are not claimed.
- **exp-022** (exp-019 pack without its 422 flawed Atlas rows, nothing added): Belebele TR 39.2 against 48.7 for exp-021. Removing
  the Atlas rows without replacing them was worse for reading, so the reviewed Atlas rows and the correspondence rows were kept.

### Writing probe (40 prompts, thinking off, AI-rated blind; AI ratings are not human review)

| | original | exp-021 |
|---|---|---|
| Naturalness (1 to 5, higher is better) | 2.43 | 3.10 |
| Invented or wrong words per answer (lower is better) | 3.27 | 1.45 |
| Task correctness (yes 1, partly .5, no 0) | 0.34 | 0.39 (no clear gain) |

More natural on 25 prompts, the original on 5, 10 tied. Free Turkish writing is smoother, not more correct.

## Regressions

Tool calls in English (-3.8 points) and IFEval without thinking (-3.1 points) went down, both inside their pre-registered limits and
within the seed noise. English reading and math did not drop.

## Conclusion

Question 1: yes for reading and grammar, not for correctness of free writing. Question 2: the spread between seeds is up to 7 points on
Turkish math, which is larger than most differences between our candidates. Question 3: the Atlas rows help; removing them hurts.

## Release and licence notes

- The model is a derivative of `LiquidAI/LFM3-1.7B` under the LFM Open License v1.0: the licence text is in the repository (Section 4(a)),
  the modified files are listed in the card (Section 4(b)), and the card states that commercial use is licensed only below US$10M annual
  revenue (Section 5).
- The dataset card credits the prompt sources: Turkce Atlas (MIT), GSM8K (MIT), MBPP (CC BY 4.0), Glaive function calling v2 (Apache 2.0),
  databricks-dolly-15k (CC BY-SA 3.0).
- 137 of 2,624 rows (about 5%) were written or corrected by an AI assistant; the owner approved their use after reviewing the provider
  terms (non-commercial research and learning project). They are labelled synthetic, never "human reviewed".

## Limits

One seed per recipe except exp-019 (two). The development sets steered earlier decisions; the 100-item final test is the cleaner check and
resolves about 8 to 10 points. The Turkish math prompts are machine translations that no native speaker validated. The correspondence rows cover one style.

## Next Step

New work moves to `experiments/preference-rl/lfm3-1.7b/` (DPO and GRPO on the 1.7B), then the MoE (LFM2.5-8B-A1B) and a diffusion model.
