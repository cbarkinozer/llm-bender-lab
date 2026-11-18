# Bilingual pilot: completed owner development review

All 20 Argilla records were submitted and exported without parsing failures on
2026-11-18. Original reviews are preserved in the ignored runtime directory:
`bilingual-runtime-local/argilla-dev20/owner-responses-*.json` and
`decoded-owner-review.json`. Raw snapshot SHA256:
`cdba37c0dee026ddb42337a98972d54e64be84d5e77c520632dd449147367e04`.
The queue randomized model identities per question; letters are not model names.

## Human preference

Pairwise score counts each question against each of the other four models,
awarding 1 for a win and 0.5 for a tie (80 comparisons per model). Mean rank
uses tied positions' average, not dense ranks. Neither measure is accuracy.
First-place counts include ties and therefore need not sum to 20.

| Model | Pairwise score | Mean rank (lower better) | First including ties | Wins/ties/losses vs original base |
|---|---:|---:|---:|---|
| Turkish-only step60 | 58.75% | 2.650 | 9 | 16/0/4 |
| Bilingual step69 | 58.13% | 2.675 | 10 | 14/0/6 |
| Bilingual step113 | 53.13% | 2.875 | 8 | 14/0/6 |
| Turkish-only step100 | 50.00% | 3.000 | 7 | 12/0/8 |
| Original base | 30.00% | 3.800 | 2 | -- |

Bilingual69 vs Turkish60 is 9 wins, 4 ties, 7 losses. Turkish60 vs Turkish100
is 7/9/4; bilingual69 vs bilingual113 is 7/7/6. The leading candidates are
practically tied on this small packet. No statistical superiority or population
accuracy is claimed. Relative preference can select the least bad wrong answer.

## Automatic diagnostics

All compared runs use the frozen matched protocol; original base is untouched
LiquidAI/LFM3-1.7B, not CPT-only. CETVEL has only 20 items per component.
TurBLiMP is a 1,600-pair diagnostic subset, not the full official benchmark.

| Model | TurBLiMP accuracy | TQuAD F1 | XQuAD F1 | EN-to-TR chrF | Summary ROUGE-L |
|---|---:|---:|---:|---:|---:|
| Original base | 71.75% | .131 | .089 | 32.27 | .143 |
| Turkish60 | 86.94% | .227 | .248 | 42.90 | .111 |
| Turkish100 | 87.06% | .187 | .259 | 43.91 | .068 |
| Bilingual69 | 87.00% | .261 | .235 | 43.70 | .047 |
| Bilingual113 | 86.81% | .278 | .277 | 44.47 | .032 |

Grammar preference and reference overlap improve in several tasks, but do not
prove faithful generation. Summary overlap drops, especially with bilingual
training; summary faithfulness needs manual inspection before assigning cause.
GECTurk exact match is zero for every model; alternative valid corrections and
format failures prevent interpreting that alone as zero spelling capability.

## Concrete remaining failures

- dev06: base alone reaches 7 minutes (with messy self-correction); all four
  SFT checkpoints confidently answer 13 minutes.
- dev13: no model solves the defective-stock arithmetic correctly. A top human
  rank here is explicitly a preference among incorrect answers.
- dev01: bilingual checkpoints are preferred but still leave Turkish spelling
  errors. dev09 JSON values are imperfect for every model.
- dev11: both bilingual checkpoints repeat until the 4,096-token limit.
  Turkish-only checkpoints also violate bullet constraints but avoid that loop.
- dev04/dev19: ambiguity handling, meaning preservation and word senses remain
  unreliable. Improved formatting is not sufficient evidence of reasoning gains.

Crosslingual15 was inspected qualitatively for the two early candidates; this
is a previously used development packet, not an independent final score.
Bilingual69 answers the TR-to-EN purchase item in English where Turkish60
answers in Turkish, but still answers the TR-to-EN repair item in Turkish.
Both mistranslate recipient absence into presence in TR-to-EN delivery.
On TR-to-TR purchase Turkish60 gets 48 while bilingual69 gets 27. Symbolic
control2 is 54 vs 10 respectively; a full reference-scored crosslingual report
is not claimed here. Both EN-to-TR purchase outputs expose `</think>` and
duplicate their explanation despite thinking-disabled inference. This merits
an output/template diagnostic; it does not by itself establish a tag mismatch
in training or justify silently changing the frozen training recipe.

## Decision and next action

Recommend freezing Turkish-only step60 as the current practical candidate and
bilingual step69 as the bilingual hypothesis candidate. Both arms use their
earlier checkpoint, consistent with the registered practical-tie policy.
There is no demonstrated decisive bilingual advantage, and neither is ready
to call production-quality Turkish. Longer training is not the next default.

On the next GPU, evaluate original base + Turkish60 + bilingual69 on the sealed
35-task four-direction packet plus 8 symbolic controls, once, under the frozen
protocol. Preserve per-direction correctness, meaning, requested language,
arithmetic, termination and raw outputs; use blind ranking plus reasoning for
owner review. Do not scale the dataset or launch another training run before
this diagnosis. The final packet remains untouched; no GPU is needed to retain
or analyze these completed development results. All four LoRAs and logs are local.
