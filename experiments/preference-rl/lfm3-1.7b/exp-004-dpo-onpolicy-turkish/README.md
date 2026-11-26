# exp-004 DPO on on-policy Turkish pairs (no editing, one signal, notebook-sized data)

## Status

`abandoned` before training (2026-11-26), a data finding. The exp-000/exp-001 control passed, so the pipeline is trusted. Samples (8 per prompt,
31,584 answers) were flagged and 3,552 pairs built (length ratio 0.99). The pre-training audit of 30 random pairs found the pairs unusable:
**27 of 30 chosen answers were wrong at task level** and only 2 pairs were usable as they are (details under Results). Nothing was trained. The
repair-based replacement is `exp-005-dpo-repaired-turkish`.

Known detector issue: about 12% of flagged "unknown words" in a random sample of 200 were real Turkish or ordinary loanword forms
(oluşturmalısınız, müzakareye, logları ...). `data/accept-words.txt` lists the ones read by hand; flags and pairs are rebuilt with it
(`tr_dpo_flags.py flag --accept-words`). The other 88% were invented words, typos or missing diacritics.

## Why

exp-003 replicated the notebook's recipe but not its data: 226 mixed pairs (14 steps) against 4,072 single-signal pairs (254 steps).
It moved nothing on held-out Turkish prompts (flagged share 50.6% to 50.0%). Rule 1 failed. The pairs also cost a lot of review: about 80%
of the flagged answers were wrong at task level and had to be dropped, so editing yields about 130 pairs per 526 prompts.

## Hypothesis

DPO over the Turkish SFT model (exp-021) with a few thousand on-policy pairs that differ in ONE thing (flagged words, broken constraints,
loops, cut-off answers) lowers the flagged share of held-out Turkish answers, with the notebook's recipe unchanged.

## Variables changed against exp-003 (documented on purpose)

| | exp-003 | exp-004 |
|---|---|---|
| Pairs | 131 Turkish (edited) + 95 skills | thousands, Turkish only, nothing edited |
| chosen | minimal repair of the rejected answer (synthetic) | a clean sample of the same prompt (exp-021's own) |
| rejected | exp-021's flagged answer | a flagged sample of the same prompt, length within 0.85-1.15 of chosen |
| Prompts | 526 (448 trainable) | 3,948: those 448 + 3,500 fresh Turkce Atlas prompts |
| Samples per prompt | 4 | 8 |
| Skills lane | yes | no (guards are measured, not trained) |

Unchanged: recipe (sigmoid + SFT, beta .1, LR 2e-5 cosine, LoRA r16, batch 2 x 8, 1 epoch), both arms (`dpo-on-sft`, `dpo-on-base`),
the held-out 78 prompts, the detectors and the rule-1 threshold. The skills lane is dropped because it was 42% of exp-003's pairs and a
different signal; that is the single-signal condition the notebook has. If the guards fall, a skills lane is the next experiment.

## Decision rules (fixed now)

1. Target: held-out flagged share of `dpo-on-sft` falls by at least a quarter (50.6% to 38.0% or lower).
2. Not by shortening or by dodging words: mean words within +-10% of exp-021 (96.4) and the share of answers that end properly not below 90%.
3. Guards (only if 1 and 2 pass): IFEval and HumanEval inside the noise of exp-021; Belebele and TurBLiMP not down by more than 1 point.
4. Because the detectors both build the pairs and measure the result, a pass on 1 needs a blind side-by-side review of 30 held-out answers
   (exp-021 against the DPO model) before it is believed.

Pairs are spot-checked before training (30 random pairs read by the owner): a pair whose "clean" answer is wrong at task level is the
expected noise; a detector false positive in the rejected answer is the risk to watch.

## Pipeline

```
python scripts/datasets/tr_dpo_onpolicy_prompts.py build --out experiments/.../exp-004.../data
bash scripts/training/pod_tr_dpo4_sampling.sh up | status | fetch DIR        # 8 samples per prompt from exp-021 (vLLM, pod)
python scripts/datasets/tr_dpo_flags.py flag --prompts P --answers A --out F --accept-from <exp-003 worksheets>
python scripts/datasets/tr_dpo_onpolicy_pairs.py build --prompts P --answers A --flags F/flags.jsonl --out DIR
bash scripts/training/pod_tr_dpo_train.sh up PAIRS "dpo-on-sft dpo-on-base"   # then pod_tr_dpo_eval.sh, held-out first
```

## Data

`data/prompts-tr-dpo4.jsonl` (3,948 rows, manifest next to it). The held-out ids are exp-003's 15% hash set; fresh Atlas prompts exclude the
500 SFT-core prompts and any near duplicate (4-gram Jaccard above 0.7) of a held-out or writing-probe prompt. Pairs and samples stay local
(not in Git), labelled `on_policy`.

## Results

No training. Data and audit only.

Pairs: 3,552 from 2,512 of the 3,948 prompts (rejected only for unknown words 2,550, broken constraint 266, English words 237, loop 40); mean
words chosen 67.3, rejected 68.3. The rejected side held a detector false-alarm rate of about 12% of flagged words in a random sample of 200
(real inflected Turkish words), fixed with `data/accept-words.txt` (57 words).

Audit of 30 random pairs (stratified by rejected reason), assessed by a strong model and cross-read by a second pass (the first-pass labels
were an AI preliminary assessment awaiting owner approval; the second pass read the 17 pairs that came with a repair and confirmed them):

| Chosen answer | Count |
|---|---|
| wrong: contradicts or invents against the given data | 10 |
| wrong: false facts from world knowledge | 6 |
| wrong: parseable words but meaningless sentences | 5 |
| wrong: broken limit or format | 5 |
| wrong: concept error | 1 |
| minor issues only | 3 (2 usable as they are) |

The word detectors flag none of these: "clean" only meant no unknown or English word. In about half of the pairs the rejected answer was also wrong
on content, so the preference carried little signal. Repair: 17 of 30 could be repaired (11 of 14 constraint prompts with data, 4 of 7 plain prompts
with data, 0 of 4 clearly open prompts: two career-advice questions, Trabzon, tides; the remaining 4 unrepaired had data blocks that the
audit regex did not recognise); 13 were returned as `rewrite_needed`. Of the 17 repairs, 3 tripped detector
false alarms (a real word, a `1-` list marker, decimal numbers counted as sentence ends) and about half were more than 15% shorter than the rejected
answer.

## Conclusion

Detector-clean on-policy samples are not good chosen answers for a 1.7B model: its answers are often wrong in content, which no word-level detector sees.
The notebook's single-signal pairs worked because every chosen answer was correct. Next: exp-005, chosen answers repaired by a strong model, only on
prompts that carry their own data.
