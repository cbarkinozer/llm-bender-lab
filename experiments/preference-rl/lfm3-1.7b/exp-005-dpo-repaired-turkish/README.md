# exp-005 DPO on repaired Turkish answers (data-carrying prompts, minimal repair, SFT-only control)

## Status

`results in, rule 6 waits for the owner` (2026-11-27). Both arms trained on the 1,008 pairs (seed 42, 189 steps), the 200 held-out prompts were answered by
exp-021, `dpo-on-sft` and `sft-only`, judged blind by an AI assistant, and the guards ran. **Rule 1 passed, rule 2 missed its threshold (59.5% against 60%),
rule 3 failed on length (mean words 0.43 of exp-021's), rule 4 passed, rule 5 failed the 1-point limit on Belebele and TurBLiMP (inside sampling noise),
rule 6 is open (an additional read of the 30 comparisons, stated by the owner to be an AI evaluation, preferred `dpo-on-sft` 23 of 24 decisive; it does not count as rule 6).** One seed, one AI judge. The rules below were fixed before any repaired data or model result existed.

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
| Length | band 0.85-1.15 | band 0.85-1.15 | chosen/rejected words 0.50-1.10 per pair and a mean of at least 0.85 over the set (mild brevity is wanted; the mean guard stops the exp-016 brevity bias; the floor was 0.70 until the pilot, see Pilot) |
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
first (131 / 61 / 8) and never repaired or trained on. Train: 2,000 prompts, 300 of them the pilot. After the pilot (plain_source repairs were usable 22%
of the time, constraint 64%) the 500 plain_source prompts outside the pilot were replaced by 500 unused constraint prompts
(`pool --drop-plain-after-pilot`; the pilot packet and the held-out set are byte-identical to before). Train by group: constraint 1,800, context 118,
plain_source 82 (the pilot only); rest packet 1,599 constraint + 101 context. The held-out set keeps its 61 plain_source prompts, so those are
evaluated although training has few: reported as a distribution gap. One finished sample per prompt, chosen by hash rank, is repaired; the manifest
`data/repair-pool-manifest.json` has the ids, the sample numbers and the input hashes.

Repair: `data/REPAIR-GUIDE.md` (rules, verdicts, two worked examples from the owner-reviewed fixes). Check: `scripts/datasets/tr_dpo_repair.py validate`
(detectors with the accept list, constraint checker with a normalisation for decimal numbers and `1-` list markers, word range 0.50-1.10, ending, `none`
and `rewrite_needed` dropped). Failed repairs get one retry with the failure reasons, then are dropped. Pairs are labelled `synthetic_repair`. The packets,
repair outputs and validation outputs under `results-local/` are committed (force-added, so the work can continue on another machine); the repairing
assistant's identity is redacted from the provenance files. The folder is git-excluded locally, so new files there need `git add -f`.

Why there is no minimal-edit similarity gate: the 17 repairs made during the exp-004 audit (by a strong model, read and judged legitimate in a second
pass) had a median character similarity of 0.40 to the original chosen answer (some started from the rejected answer instead), so a 50% gate would
have discarded most good repairs. The similarity is recorded and reported per verdict, and `larger` pairs are over-sampled in the owner's reads.

## Training Setup

LoRA DPO + SFT (`scripts/training/run_tr_dpo_train.py`), seed 42, 3 epochs (about 200 steps for 1,000-1,300 pairs; the notebook ran 255 steps), arms:
`dpo-on-sft` (default) and `sft-only` (`--dpo-weight 0`, same chosen answers). Pod launch through the session script's stages `exp005-dpo-on-sft` and
`exp005-sft-only`. At least 1,000 usable pairs are needed; if fewer, a second sample per prompt (`alt_sample`) is repaired.

## Evaluation

Held-out answers from exp-021, `dpo-on-sft` and `sft-only`, same decoding (temperature 0.1, top_k 50, repetition penalty 1.1, max 800 new tokens,
thinking off, one answer per prompt; a temperature-0.7 second answer is a reported sensitivity check). Judge: a model of a different family than the
repair model, blind and order-randomised, instructions fixed in `data/JUDGE-GUIDE.md` before any answer exists, ties allowed. Run by an AI assistant
with `scripts/evaluation/tr_dpo_judge.py`: sheets show only the prompt, two anonymous answers and their word counts, the key stays closed until a
set is finished, batches of 25 are final once saved. This is a model's judgement, not an independent human check. Secondary set: exp-003's
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

## Pilot (2026-11-26, before any training)

300 pilot items repaired by the strong model (`results-local/repair-output-pilot.jsonl`): 118 proposed repairs (57 minimal, 61 larger), 177
`rewrite_needed`, 5 `none`. First validation: 103 usable pairs (34%): constraint 88 of 201, context 7 of 17, plain_source 8 of 82; 15 repairs failed
the code check (11 unknown words, 3 endings, 2 English words). The yield gate (50%) was not met. Reading the 177 `rewrite_needed` reasons: 84 items (28%
of the pilot) are mostly invented content that no repair rule saves, and 79 cite the lower word bound (27 of them nothing else): the 0.70 floor made
the repairer refuse answers whose invented parts, once removed, leave fewer than 70% of the words. Changes made before any training: floor 0.50, a
mean-ratio guard of 0.85 over the pair set (the shortest pairs are dropped until the mean is met), and a second pass for the 94 rows above
(`retry-input.jsonl`: 15 failed checks with their reasons, 79 range-widened) with a guide that says never to pad. The gate itself is unchanged and is
re-checked after the second pass, together with the owner's read of 30 pairs.

Second pass (94 rows): 52 repairs, 42 `rewrite_needed`. Validated together with the first pass: **155 usable of 300 (51.7%)**: constraint 128 of 201
(64%), context 9 of 17, plain_source 18 of 82 (22%); 94 `larger`, 61 `minimal`; median length ratio 0.83, median character similarity 0.60. The
yield gate is met, narrowly. The brevity guard (mean ratio 0.85) then drops 9 of the shortest `larger` pairs, leaving 146 pairs (48.7% of the pilot;
the gate is counted on usable repairs before the set-level guard). One ending-check fix: a JSON answer that ends with `}` was flagged (3 rows in
pass 2), `}` now counts as a finished ending. Scaled to the train pool (1,300 / 118 / 582) the yield predicts about 1,000 usable repairs and about 950
pairs after the guard, under the 1,000 minimum, and 582 plain_source prompts would cost most of the repair effort for about 130 pairs.
Owner read: 30 random pilot pairs (18 `larger`, 12 `minimal`; 23 constraint, 4 context, 3 plain_source), Argilla dataset
`exp005-pilot-pairs-read-30`, publisher `scripts/datasets/publish_exp005_pair_review.py`.

Read result: 27 of 30 `good` and `chosen_better`, 3 of 30 `minor_issues` (missing targets, padding or item count, items not concrete enough; complete
corrections written in the Argilla text boxes). **The 27 / 30 labels were entered by an AI assistant, not by an independent human**, and the same
assistant family did the repairs, so it is a weak check. The owner glanced through the pairs for anomalies and found none (natural, good-quality
Turkish), without labelling them in the tool. The gate is counted as passed on that combined evidence; the independent checks come later (blind judge in rule 1-2, the
owner's blind read of 30 held-out answers in rule 6). The 3 corrected answers were to replace those chosen answers when the final pairs are built (outcome: see Rest packet). The repair guide got one sentence from these three cases
(cover every named target, N concrete items, no filler item); the 1,700 rest items are repaired under it.
After the read the train pool changed (see Dataset): plain_source dropped from the rest packet, 500 constraint prompts added.

## Rest packet (2026-11-27, before any training)

The 1,700 rest items were repaired in six parts (`data/REPAIR-PROMPT.md`, the same assistant as the pilot, under the guide with the one added sentence).
Usable after code validation per part: 129 / 160 / 160 / 155 / 168 / 148 of 284 / 284 / 284 / 284 / 284 / 280 (920 of 1,700 = 54% before the retry). One retry batch
of the 32 repairs that failed the code check (unknown or English words, one flagged) went back once (`data/REPAIR-PROMPT-ROUND2.md`, a prompt with
`failure_reasons` and `previous_chosen`): 30 recovered, 2 stay dropped. **Rest total: 950 usable of 1,700 (55.9%)**: constraint 893 of 1,599, context 57 of
101; 577 `larger`, 373 `minimal`; median length ratio 0.81, median character similarity 0.55; 731 `rewrite_needed`, 17 `none`. With the pilot (155) that is
1,105 usable repairs of 2,000, and **1,011 pairs after the brevity guard** (mean ratio 0.85, 94 shortest dropped): constraint 939, context 58,
plain_source 14. The median length ratio per part ranged from 0.75 to 0.86 (0.83, 0.80, 0.75, 0.86, 0.82, 0.78), which is why the guard drops more pairs than
in the pilot.

Second-sample round: the first 150 train prompts without a usable repair (hash rank, `tr_dpo_repair.py alt`, manifest `data/repair-alt-manifest.json`) got
their `alt_sample`, a different answer of the same model, repaired. 56 of 150 usable (37%, median length ratio 0.58), so the yield is lower than for the first
sample. The pre-registered rule says the alt round is used only when fewer than 1,000 pairs exist; the main set already has 1,011, so **the alt repairs
are not used in training** (with them the set would have 1,034 pairs; they stay in `results-local/alt-validation/`).

Three pilot pairs: the three marked `minor_issues` in the read had a complete correction written by the AI assistant (not an independent human;
`results-local/repair-output-pilot-corrections.jsonl`). The corrections went through the same validator as every other repair
(`results-local/pilot-validation-corrected/`): one is usable and replaces its chosen answer (`dpo4-atlas-272645`), two fail the length band (ratio 1.36 and a
short answer changed by more than 5 words), so those two pairs (`dpo4-atlas-069143`, `dpo-c-trgen-0242`) are dropped. The pilot then has 153 usable repairs of
300 (51.0%, the 50% gate still met).

**Final pair file:** 1,103 usable repairs (153 pilot + 950 rest) give **1,008 pairs** after the brevity guard (95 shortest dropped, mean ratio 0.85):
constraint 937, context 57, plain_source 14; 590 `larger`, 418 `minimal`; unique ids, no overlap with the held-out ids (checked in code). Short answers
(under 20 words) are allowed to move by 5 words, so single pairs reach a length ratio of up to 1.62.

## Results

**Training** (RTX 4090, 189 steps each, about 8 minutes of training and 15 with the checks and merge; `results-local/train-fetch/`). Rule 4 passed for both
arms: the logged `logps/chosen` went from -64.2 at the first logged step to -54.5 (`dpo-on-sft`) and -50.7 (`sft-only`) at the last, it did not fall. Reward
margin at the end 4.96 (`dpo-on-sft`) and 3.14 (`sft-only`); both reach implicit-reward accuracy 1.0 on the training pairs, because the SFT term alone also
lifts the chosen answers over the reference. Training accuracy therefore does not separate the arms.

**Blind judging** (200 held-out prompts, temperature-0.1 answers, ties and identical answers not counted as decisive; `results-local/judging/`):

| set | comparison | decisive | wins of the first | share | Wilson 95% | ties | identical | rule |
|-----|------------|---------:|------------------:|------:|-----------:|-----:|----------:|------|
| A | `dpo-on-sft` vs exp-021 | 169 | 146 | 86.4% | 80.4-90.8 | 29 | 2 | rule 1: **passed** |
| B | `dpo-on-sft` vs `sft-only` | 126 | 75 | 59.5% | 50.8-67.7 | 63 | 11 | rule 2: **missed** (threshold 60%, lower bound above 50%) |
| C | `sft-only` vs exp-021 | 170 | 150 | 88.2% | 82.5-92.3 | 27 | 3 | not a rule; run because rule 1 passed and rule 2 did not |

Sanity check of the procedure before set A: 30 training pairs (repaired against original answer, key apart): the repaired answer was chosen 30 of 30, so the
procedure agrees with the repair on clear cases; it does not show sensitivity on fine differences. The share of `A` among decisive judgements was 53%,
57% and 54% (position check, inside 40-60%).

Length confound, reported as a robustness split (added to the guide before any judgement): in A and C the shorter answer wins 78% and 82% of the decisive
comparisons; among comparisons whose word counts are within a factor of 0.75-1.33 the share is 82.2% (37/45, Wilson 68.7-90.7) in A, 61.2% (52/85,
50.5-70.8) in B and 82.0% (41/50) in C. By prompt group the first-named arm wins 96 of 111 constraint, 44 of 51 plain_source and 6 of 7 context decisive
comparisons in A. Most of the wins in A come from criterion 1 (105 of 146: invented or inverted content in exp-021), then criterion 2 (limits and format).

**Additional read of 30 comparisons** (set O, `results-local/judging/owner-read/`): the 30 sheets (`dpo-on-sft` against exp-021, answer order randomised, key
closed until the read came back) were answered by the owner on 2026-11-27 with the note that the read is an additional AI evaluation. Because the guide
defines rule 6 as the owner's own human read, **this does not count as rule 6, which stays open**. Result: `dpo-on-sft` preferred in 23 of 24 decisive
comparisons (95.8%, Wilson 79.8-99.3), 6 ties, A/B position share 50%, no deciding criterion recorded. The shorter answer won 23 of the 24 decisive ones
and only 5 pairs are length-matched (4 won), so the read repeats the length confound and cannot separate it. The owner's notes: a tie is not "good"
(item 15: both answers add unsupported information; item 22: both present an undecided decision as decided), and the preferred answer in items 10 and 25
also breaks the greeting/question ban. Sets A to C were judged by this repo's AI assistant; the read adds a second AI view, not a human one.

**Side checks, rule 3** (`results-local/heldout-checks/`, 200 answers per system, temperature 0.1; the temperature-0.7 answers give the same ordering):

| system | mean words | ended with the end token | constraint pass | detector flagged share |
|--------|-----------:|-------------------------:|----------------:|-----------------------:|
| exp-021 | 68.3 | 97.5% | 75.6% | 39.5% |
| `dpo-on-sft` | 29.7 | 100% | 93.1% | 16.0% |
| `sft-only` | 34.0 | 99.5% | 91.6% | 19.0% |

Constraint pass, ending and flagged share all improved. The mean words did not stay within 0.80-1.10 of exp-021's: the ratio is **0.43** (`dpo-on-sft`)
and 0.50 (`sft-only`), so **rule 3 fails** on its length clause. Cause seen in the data: the chosen answers in the pairs average 34 words (rejected 42),
because only answers that could be repaired short of a rewrite became pairs, and both arms learned that length (by group, mean words in `plain_source`
fell from 109 to 32 although that group has only 14 training pairs).

## Regressions

Guards (`results-local/guards.json`, same session and decoding as exp-021; difference to exp-021 in points, interval = paired 95%):

| guard | exp-021 | `dpo-on-sft` | `sft-only` |
|-------|--------:|-------------:|-----------:|
| IFEval strict, thinking off (541) | 71.5 | 68.2 (-3.3, [-7.1, +0.4]) | 68.9 (-2.6, [-6.1, +0.9]) |
| IFEval strict, thinking on (270) | 84.1 | 87.4 (+3.3, [-0.4, +7.1]) | 87.0 (+3.0, [-0.3, +6.2]) |
| HumanEval off / on (164) | 73.2 / 92.7 | 75.6 / 92.1 | 75.6 / 92.1 |
| Belebele EN restricted | 70.0 | 67.6 (-2.4) | 69.4 (-0.6) |
| Belebele TR restricted | 48.7 | 46.3 (-2.3) | 47.1 (-1.6) |
| TurBLiMP macro | 85.9 | 84.8 (-1.1) | 85.8 (-0.1) |
| math final test, thinking on, group rate | 90.5 | 91.5 | 92.5 |
| math EN / TR (eval v2) | 92.8 / 73.7 | 93.4 / 72.4 | 94.7 / 77.0 |
| tool calls EN / TR | 91.2 / 81.2 | 93.8 / 82.5 | 93.8 / 82.5 |

IFEval and HumanEval are inside the noise (every paired interval contains 0). **Rule 5 fails as registered** (Belebele and TurBLiMP not down by more than 1
point): `dpo-on-sft` is down 2.4 and 2.3 on Belebele EN and TR and 1.1 on TurBLiMP, `sft-only` 1.6 on Belebele TR. These differences are smaller than the
Belebele sampling interval (about plus or minus 3 points at n=900), but the rule is not loosened here. The hint that the DPO arm loses a little more reading
and grammar ability than the SFT-only arm is within noise and needs the second seed. Not run in this session: the diagnostic and the writing probe
(not registered guards) and the owner's read (rule 6).

## Conclusion

On held-out data-carrying prompts both trained arms are judged better than exp-021 in most decisive comparisons (86% and 88%), with fewer invented facts,
more kept limits and no unfinished answers; rule 1 passes. The same trained answers without the preference term do about as well (`sft-only` 88% against
exp-021), and `dpo-on-sft` beats `sft-only` in 59.5% of decisive comparisons (Wilson 50.8-67.7), just under the registered 60%. **The finding is therefore:
SFT on the repaired answers explains most of the gain; the preference term is not shown to add, at best a small edge** (61% on length-matched pairs, not
enough against the threshold). The gain comes with a large shortening of the answers (mean words below half of exp-021's) that was not intended and
that fails rule 3, and with Belebele and TurBLiMP changes that miss the 1-point limit for `dpo-on-sft` (inside noise). Neither arm replaces exp-021 as
published. One seed, one AI judge, the owner's blind read (rule 6) open: no public claim before the second seed.

## Next Step

1. Rule 6 (owner's own human blind read of the 30 comparisons, `results-local/judging/owner-read/judge-sheet-O-batch-01.md`) is still not done: the read
   that came back was declared an AI evaluation (23 of 24 decisive for `dpo-on-sft`, shorter answer winning 23 of 24) and is recorded as an additional
   read only.
2. If the line goes on: a pair set that does not shorten (repairs chosen without the short-answer selection, or a length-controlled chosen and rejected
   pair as in exp-003's lessons) and a second seed; the SFT-only arm stays as the control.
3. Later: publish the pairs on the Hugging Face Hub as a public dataset repo (owner's plan; wording of provenance decided then).
