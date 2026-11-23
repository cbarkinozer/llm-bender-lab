# exp-021 / exp-019 seed 2 / exp-022: reviewed Turkish rows and email rows, with controls, 2026-11-23

## Status

Design frozen 2026-11-23 10:30 UTC, before any result of these runs existed. Results are added below after the pod session.

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
