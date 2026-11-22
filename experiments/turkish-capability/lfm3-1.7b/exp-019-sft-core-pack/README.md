# exp-019: LFM3 pack of SFT core v01, CPT parent (exp-020: same data on the original base), 2026-11-22

## Status

Design frozen before any result of the trained models existed (written while the base-model sampling for the pack was still
running; the base final-test numbers had not been read). Results are added below after the run.

## Goal

Find out whether the model's own verified answers to the SFT core v01 prompts (math, code, tool calls, English general replay,
native Turkish tasks, Turkish translations of math problems) teach Turkish reading without the exp-016 side effects. This is
the owner's goal: decent Turkish with tools, math, coding and instruction following kept. The data are also the starting
point for the owner's MoE and text-diffusion experiments (the core is reusable, the pack is LFM3-specific).

## Hypothesis

Because exp-016 trained Turkish prompts on English-twin reasoning, kept the shortest sample and dropped long answers, it taught
the model to think briefly about Turkish problems (median 957 tokens against 1,581 for the base) and cost 7 points of Turkish
math. Training on the model's own reasoning for the Turkish prompt itself, chosen at random among verified samples, with no
length cap, keeps the Turkish math at the base level while the replay rows keep English, tools and coding. This is a hypothesis
from the exp-016 and exp-018 logs, not a proven cause.

## Parent experiments

[exp-016](../exp-016-self-distill-targets/README.md) (arm B: same parent, shorter targets from English twins),
[exp-017](../exp-017-understanding-diagnostic/README.md) (the diagnostic cells), [exp-018](../exp-018-english-guard/README.md)
(English guard), data: [sft-core-v01](../sft-core-v01/README.md), plan: [SFT-CORE-PLAN-20261122.md](../SFT-CORE-PLAN-20261122.md).

## What changed against exp-016 (several things at once; this is a recipe comparison, not a single-variable test)

| | exp-016 arm B | exp-019 |
|---|---|---|
| Rows | 516 (129 groups x 4 directions) | the pack (about 3,000 rows, built from verified samples) |
| Turkish prompts | 160 human prompts, targets from English twins, Turkish renderings by Claude | 1,000 GSM8K problems translated by OpenAI Codex, 500 native Atlas tasks; targets are the base model's own reply to the Turkish prompt |
| Selection | shortest sample, answers over 1,500 characters dropped | random verified sample, nothing cut by length (limit 8,000 tokens) |
| Reasoning | English twin's | the model's own on the Turkish prompt (English think block) |
| Thinking mode | about 16% on | 80% on, 20% off |
| Length | max_length 4096, batch 2x4, 55 steps | max_length 8192, batch 1x8, one epoch (about 370 steps), same LoRA r32/alpha64 and LR 1e-4 |

### The pack as trained (2,909 rows, `train.jsonl` sha256 starts `caf7c09ffe15ec6b`, built 2026-11-22)

| Category | Rows | Notes |
|---|---:|---|
| math, English | 962 | 769 thinking on, 193 off |
| math, Turkish | 686 | 578 on, 108 off; the base solved 78.5% of the Turkish groups; about 21% of its verified Turkish samples were English replies or had English words in the answer and were filtered out |
| Turkish general (Atlas) | 422 | 326 on, 96 off; unknown-word, English-leak and English-reply filters |
| English general (Dolly) | 299 | natural lengths |
| tool calls, English | 292 | |
| code, English | 248 | thinking-off code rows are few (35): the base fails MBPP without thinking |
| Thinking on | 81.5% | |

Pack-building decisions: a first build applied the unknown-word limit (Zeyrek candidate rate above 4%) to every Turkish row and
dropped 28% of the verified Turkish math groups, because short math answers repeat character names that Zeyrek does not know.
It was changed before any training to apply that limit only to the free-form Atlas answers; math rows keep the English-reply and
English-leak checks. The first report is kept in `pack-local/` (ignored). Length drift against the natural verified lengths:
Turkish math thinking on 1.14 (kept answers are longer, median 1,282 against 1,126 tokens), other cells 1.00 to 1.06, the
opposite direction of exp-016. Solution-step bucket survival of Turkish math groups: 38%, 38%, 31%, 30% (buckets 1 to 4; counts
include thinking-off groups), a mild bias against harder problems.

Parent: the Turkish CPT merge (as arm B). exp-020 repeats the run on the original pinned base (shows how much of the effect
comes from the data alone, which matters for models without our CPT).

## Pre-registered rules (thinking on, the owner's assumed mode; paired by item with a bootstrap 95% interval)

Base and arm B numbers are the earlier ones from exp-017 (diagnostic cells, 152 items x 4 seeds), exp-016/exp-018.

| Gate | Measure | Rule |
|---|---|---|
| G1 primary: Turkish math reading | diagnostic cell D (Turkish problem, Turkish reply, 152 items x 4 seeds) | model - base >= -0.03 AND lower bound of (model - arm B) > 0 (base .691, arm B .612) |
| G2 fresh test | the 100 GSM8K test items translated and AI-reviewed, never trained on, thinking on, 4 samples each: Turkish and English | Turkish >= base - 0.03 and English >= base - 0.03 (point estimates; intervals reported) |
| G3 Turkish reading, general | Belebele Turkish, restricted (base .352, arm B .483) | >= .45 and not more than .03 below arm B |
| G4 grammar | TurBLiMP frozen subset | >= .85 |
| G5 reply language | writing probe (40 native prompts, thinking off), answers entirely in English | at most 1 of 40 (arm B: 4 of 40) |
| G6 English guard | exp-018 rule on IFEval strict (270) and HumanEval, thinking on | delta >= -0.05 and lower bound >= -0.10 against the base |
| G7 tools and English math | eval v2 thinking on: tool calls TR and EN, English math | each >= base - 0.05 |

The run passes only if G1 to G7 all pass; otherwise the failing gates are reported and the run is not called a v1 candidate.
Reported but not gating: IFEval thinking off on the full 541 prompts (exp-016 arm B lost 8.9 points; the length hypothesis
predicts a smaller loss now, target > -0.05), symbolic arithmetic, diagnostic cells A, B, C, F, G, the share of Turkish math
items the base never solved, answer lengths.

Sensitivity subset for G2 (added 2026-11-22 after reading the base model's final-test results but before any trained-model
result, chosen from data properties and not from model scores): the final test without c-mathtest-0008, -0027 and -0082 (they
write thousands as `120,000`, which Turkish reads as the decimal 120.0) and c-mathtest-0068 (the Turkish says each later hour
costs twice the previous hour, the English says twice the first hour). The base model scores .9375 on the English final test and
.7625 on the Turkish one; the three format items are all at 0.0 in Turkish. The gate stays on all 100 items; the 96-item result
is reported next to it.

Detectable differences: 152 items x 4 seeds resolve roughly 4 to 5 points; the final test (100 items) about 8 to 10 points, so
G2 can only show "no large drop", not an improvement.

## Threats to validity

- The 152 eval items and Belebele have steered earlier decisions (development data); the final test is the clean check.
- The training translations (OpenAI Codex, AI-reviewed) and the eval translations (malhajar machine translation) differ; both are
  measured. Translation errors that change an answer (found: c-mathtest-0068) lower scores for every model equally.
- Verified samples exist only for problems the base already solves; the unsolved ones are not trained on (selection bias,
  reported per solution-step bucket in the pack report).
- One training seed per run; thinking-on sampling noise; the guard rule is relative to the base, not an absolute bar.
- Several recipe changes at once: a pass does not say which change mattered.
- Provider terms: translations were produced under a stated non-competing research scope (see the dataset card); nothing
  derived from them is published without a separate decision.

## Results (exp-019, RTX 4090, one training seed, 2026-11-22; summaries in `results/`, raw runs in ignored `results-local/`)

Training: 364 steps, 17.6 minutes, final train loss .458, all audits and the adapter reload check passed (3.70M tokens, 3.40M
supervised, none truncated). The merged model reloads exactly. Gates (thinking on, base and arm B numbers from the earlier runs):

| Gate | Result | Verdict |
|---|---|---|
| G1 Turkish math reading, diagnostic cell D | .752 (base .691, arm B .612); vs base +.061 [+.021, +.104]; vs arm B +.140 [+.092, +.189] | PASS |
| G2 fresh final test, Turkish | .770 against base .7625 (+.0075 [-.040, +.055]) | PASS (no gain either) |
| G2 fresh final test, English | .930 against base .9375 (-.0075 [-.030, +.018]) | PASS |
| G3 Belebele Turkish, restricted | .480 (base .352, arm B .483); English .707 (base .670) | PASS |
| G4 TurBLiMP macro | .854 (arm B .868, CPT .869, base .718) | PASS by .004 |
| G5 writing probe, answers entirely in English | 0 of 40 (arm B: 4 of 40) | PASS |
| G6 English guard, thinking on | IFEval strict +.030 [-.011, +.070]; HumanEval -.012 [-.043, +.018] | PASS |
| G7 eval v2 | tools EN .925 (base .950), tools TR .850 (.825), math EN .947 (.954), symbolic EN .983 / TR 1.0 | PASS |

All seven pre-registered gates pass.

Other diagnostic cells (thinking on, 152 items x 4 seeds; base / arm B / exp-019): A (EN problem, EN reply) .949 / .944 / .949;
B (EN problem, TR reply) .952 / .933 / .938; C (TR problem, EN reply) .729 / .602 / .755; D .691 / .612 / .752; F (restate first)
.717 / .617 / .773; G (translate first) .551 / .646 / .625. Eval v2 Turkish math, one seed: .717 (= base, arm B .592).

Final test without the four flawed items (96 items, sensitivity subset): English .9453 against base .9479; Turkish .7969 against
.7943 (+.0026 [-.044, +.050]). Thinking length on the Turkish final test: median 1,379 tokens (base 1,326, arm B about 957 on the
diagnostic), so the brevity cut of exp-016 is gone.

Reported, not gating: IFEval strict with thinking off on the full 541 prompts .710 against base .730 (-.020 [-.057, +.017]; exp-016
arm B lost .089); HumanEval thinking off -.006; IFEval thinking off (270) +.004. The 7 of 40 writing-probe answers that did not end
with EOS hit the probe's 800-token cap (long structured answers such as the base also gives; arm B answered with about 83 words
on average), they are not loops.

## Regressions

None beyond noise on the gates. TurBLiMP is 1.4 points below arm B (.854 against .868) and clears its gate by .004. Tool calls in
English are 2.5 points below the base (interval touches zero). The Turkish reading gap itself remains: English .949 against
Turkish .752 on the diagnostic, .93 against .77 on the final test.

## Conclusion

The pack removes the exp-016 side effects: Turkish math reading is back at the base level or slightly above on the development
items (D +.061, F +.056, C +.026) while the clean final test shows no difference (it cannot resolve less than 8 to 10 points),
English, coding, tool calls and instruction following are kept, the thinking-off IFEval loss shrank from 9 to 2 points, Belebele
Turkish keeps arm B's gain (+.13 over the base) and Turkish replies no longer drift into English on the writing probe. This is
consistent with the hypothesis that exp-016's brevity bias caused the Turkish-math loss and the IFEval length loss; it does not
prove it (several things changed at once). It does not close the Turkish reading gap. One training seed: a v1 candidate, not a
confirmed result. The "improvement over the base" on D comes from development items that already steered earlier decisions.

## Next step

Second training seed of exp-019 (about 40 minutes of GPU) before any publication; the owner's read of about 40 Turkish answers
(naturalness and correctness scored separately) and the 60-row review of the Atlas rows; wait for exp-020 (same data on the
original base) to see how much is the data alone. Publishing needs a separate decision and the provider-terms caveat in the
dataset card. The code and tool sheets are not needed for this result; they would add Turkish code and tool rows.
