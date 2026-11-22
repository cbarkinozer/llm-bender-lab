# exp-017: understanding diagnostic (inference only, 2026-11-22)

## Status

completed (diagnostic; no model was trained). The writing probe was rated by an AI assessor (OpenAI Codex), not by a human;
the owner (a native speaker) added a qualitative opinion on excerpts, but no full human rating of the 160 answers exists
(see "Writing review" and "Owner's qualitative assessment").

## Goal

Find where the Turkish gap comes from (reading, writing, or reasoning in Turkish) so the next training signal targets the
right thing.

## Hypothesis

LFM3 solves a GSM8K problem in English but not in Turkish mostly because it misreads the Turkish problem. Writing Turkish
and reasoning in Turkish are secondary costs, and the exp-016 Turkish targets (short final-answer renderings) may have
taught short answers instead of understanding.

## Parent experiment

[exp-016](../exp-016-self-distill-targets/README.md) (arms A and B are evaluated here; nothing is retrained).

## What changed

Nothing in any model. This experiment crosses problem language x reply language x translate-first on the eval v2 math
items, adds Belebele (EN/TR) and a 40-prompt Turkish writing probe, and measures unknown words with a morphological analyzer.

## Base model and revisions

`LiquidAI/LFM3-1.7B@0dc4268b561499c648c7ba7c9466bf3d8d01517a`; CPT adapter `cbarkinozer/LFM3-1.7B-Turkish-CPT@6f213ec25a94`
merged into it; arms A and B are the exp-016 merges (`adapters-meta/` there). Software: vLLM 0.34.0rc1.dev251, torch
2.14.0+cu130, transformers 5.20.2 (full details in each `results/*/run-manifest.json`).

## Dataset

Eval items only (never training data): the 152 paired GSM8K items of eval v2; Belebele `facebook/belebele@7899cdfa4e1e`
(eng_Latn and tur_Latn, 900 aligned items, CC-BY-SA 4.0, kept out of Git); 40 hand-written Turkish prompts
(`../eval-v2/writing-prompts-tr.jsonl`, built by `scripts/datasets/build_lfm3_writing_prompts_tr.py`).

## Training setup

None (inference only, GPU RTX 4090, about 3 hours including the queue).

## Evaluation

Described under Design below; scripts: `scripts/evaluation/run_lfm3_understanding_diagnostic.py`,
`score_lfm3_understanding_diagnostic.py`, `lfm3_belebele_eval.py`, `run_lfm3_writing_probe.py`,
`score_lfm3_writing_probe.py`, `turkish_nonword_rate.py`, pod drivers `run_lfm3_understanding_*_session.sh` and
`run_lfm3_understanding_supervisor.sh`.

## Design (frozen before results were seen; smoke run on 6 pairs checked plumbing only)

Items: the 152 paired GSM8K items of [eval v2](../eval-v2/README.md), same packet checksums. Sampling: model-card math
preset (T 1.0, top_p .95, top_k 20), 4 sampling seeds (3407-3410) per cell, thinking off (2,048 new tokens) and on
(8,192). Models: base (primary), arm B = CPT parent + self-distilled SFT (primary), arm A = base + self-distilled SFT
(secondary, exploratory).

| Cell | Problem | Reply | Prompt |
|---|---|---|---|
| A | en | en | eval v2 English prompt (reference) |
| B | en | tr | English problem, "write your whole reply in Turkish", marker `Nihai cevap` |
| C | tr | en | Turkish problem body, English instruction, "write your whole reply in English" |
| D | tr | tr | eval v2 Turkish prompt (current result) |
| F | tr | en | Turkish problem body, "first restate the problem in English, then solve in English" |
| G | tr | en | greedy translation by the same model (thinking off), then the English solve prompt on that translation |

Scoring: eval v2 math scorer (lenient `correct_any`; strict marker rate also reported); accuracy per item is the mean
over seeds; intervals are item-level bootstrap (4,000 resamples), paired differences use the same items. G also reports
whether every digit string of the Turkish problem survived the translation (`numbers_preserved`). Reply language is
checked with a stop-word heuristic. Wrapper wording differs between cells (the instruction language and reply instruction
are part of each condition), so differences are condition effects, not pure language effects.

## Pre-registered reading of the results (point estimates; "close" = within 0.06, about 9 items)

Primary quantities: A-D (total gap), A-C (reading cost), A-B (writing cost), G-C and G-D (value of translating first).

1. A-D small (under 0.10) in a mode: no gap there, nothing to fix in that mode.
2. A-C under 0.06 and A-D over 0.10: the model reads Turkish fine; the loss is reasoning or writing in Turkish. Next:
   keep reasoning in English, train answer language and format only; understanding data is not the bottleneck.
3. A-C over 0.15 and G at least C+0.10 and G within 0.10 of A: the model reads Turkish badly when it reasons directly but
   can translate. G is then a no-training baseline that any training run must beat. Next: exp-018 distills
   "Turkish prompt -> the model's own answer to its English version" (teacher sees the English version).
4. G more than 0.15 below A, or `numbers_preserved` rate below 0.85: translation itself is lossy, so comprehension is
   missing. Next: Turkish/English parallel data (not task data) before any task distillation; re-check with Belebele.
5. A-B over 0.10: writing Turkish costs accuracy even with an English problem. Turkish answers should stay short
   final-answer renderings plus English reasoning.
6. Arm A or B differ from base by more than 0.10 in cells C, D, F or G: the SFT changed reading, not only format; check
   the cap rate and answer length before interpreting.

If the pattern fits none of these, report that and do not pick a training design from it.

## Threats to validity

- Machine-translated items (about 4 of 26 inspected failures had translation flaws, e.g. "15 ayak" for feet), so a part
  of the gap is test noise; the Turkish side is a lower bound on what a clean Turkish test would show.
- Single benchmark family (grade-school math) and one problem style; Belebele (Turkish/English) is the planned second
  measure of understanding outside math.
- Condition wrappers are not matched word for word; sampling at T 1.0 adds variance, mitigated by four seeds.
- Cell G uses the model as its own translator; flawed translations count against it, as intended for a no-training baseline.
- Mean tokens and cap rates are reported because thinking-off Turkish answers can fail by not stopping, not by
  misunderstanding.

## Results (RTX 4090, vLLM, 152 items x 4 seeds per cell; summaries in `results/`, raw answers stay in ignored `results-local/`)

Accuracy (mean over seeds; item-level bootstrap intervals are in each `summary.json`):

| Model, mode | A en/en | B en/tr | C tr/en | D tr/tr | F restate | G translate first | G digits kept |
|---|---:|---:|---:|---:|---:|---:|---:|
| base, thinking on | .949 | .952 | .729 | .691 | .717 | .551 | 117/152 |
| base, thinking off | .891 | .766 | .539 | .413 | .541 | .467 | 117/152 |
| arm B (CPT + SD), on | .944 | .933 | .602 | .612 | .617 | .646 | 116/152 |
| arm B, off | .870 | .520 | .480 | .270 | .474 | .571 | 115/152 |
| arm A (base + SD), on (exploratory) | .957 | .942 | .605 | .610 | .569 | .534 | 110/152 |
| arm A, off (exploratory) | .885 | .576 | .428 | .286 | .454 | .495 | 110/152 |

Reading cost A-C: base .22 (on) / .35 (off); arm B .34 / .39; arm A .35 / .46. Writing cost A-B: base 0.00 (on) / .125 (off);
arm B .01 / .35; arm A .02 / .31. "SD" = exp-016 self-distilled SFT.

Belebele (900 paired items, thinking off, greedy; accuracy by first-token log-probability among A-D, "restricted"; chance .25):

| Model | EN | TR | TR-EN gap | TR vs base (paired) |
|---|---:|---:|---:|---|
| base | .670 | .352 | -.318 | - |
| CPT merged | .604 | .264 | -.340 | -.088 [-.121,-.053] |
| arm A | .660 | .449 | -.211 | +.097 [+.059,+.136] |
| arm B | .693 | .483 | -.210 | +.131 [+.088,+.173] |

Arm B vs arm A, Turkish: +.034 [+.006,+.064]. English restricted accuracy is unchanged by SFT (A -.010, B +.023, both include
0), so the Turkish gain is not just answer-format calibration; the generated-text reading (format failures count as wrong)
agrees (base TR .353, A .441, B .478).

Writing probe (40 native Turkish prompts, thinking off; `results/writing/`; ratings are in "Writing review" below):

| Model | answers without EOS | 12 constraint prompts passed | mean words | unknown-word tokens | of which English | non-English candidates |
|---|---:|---:|---:|---:|---:|---:|
| human Turkish (Belebele passages) | - | - | - | 2.2% | 0.4% | 1.8% (names, loanwords) |
| base | 10% | 5 | 139 | 3.3% | 0.9% | 2.3% |
| CPT merged | 70% | 0 | 276 | 0.5% | 0.2% | 0.2% |
| arm A | 2.5% | 7 | 88 | 2.0% | 0.8% | 1.2% |
| arm B | 2.5% | 5 | 83 | 5.1% | 4.3% | 0.8% |

Four of arm B's 40 answers are entirely in English: three of the six e-mail prompts and the "translate this sentence into
Turkish" prompt (arm A: one e-mail; base: the translation prompt partly).

## Reading against the pre-registered rules

- **Rule 1 (no gap): does not fire anywhere.** A-D is .26 (base on) to .60 (arm B/A off).
- **Rule 2 (reading fine, writing/reasoning is the loss): does not fire.** A-C is at least .22 in every cell.
- **Rule 3 (translate-first is a rescue): does not fire.** G beats C by at least .10 nowhere; the closest is arm B off (+.09).
- **Rule 4 (translation lossy, comprehension missing) fires for every model and mode**: G is .30 to .42 below A and only
  75-77% of translations keep every digit string. Uncertainties: the translation was one greedy thinking-off sample (as
  designed), the digit check can undercount legitimate rewordings, and for the base with thinking on, reading directly (.73)
  beats translating first (.55), so the model's implicit reading is better than its explicit translation. Rule 4 says "no
  comprehension", the data say "partial comprehension, weak explicit translation".
- **Rule 5 (writing Turkish costs accuracy) fires with thinking off for all three models** (base .125, arm A .31, arm B .35)
  and not with thinking on (|A-B| at most .02). The prescription in the rule ("keep Turkish answers short renderings") is
  contradicted by the arms: they were trained on exactly such renderings and lost most there. The cleaner reading is that
  Turkish replies are free when the reasoning happens in the English think block and expensive when the reply itself has to
  carry the reasoning.
- **Rule 6 (SFT changed reading, not only format) fires.** Against the base, thinking on: C -.12 (A) / -.13 (B), F -.15 / -.10,
  D -.08 / -.08. Thinking off: D -.13 (A) / -.14 (B). So the exp-016 SFT lowered the reading of Turkish math problems in both
  modes while English stayed level. G rises for arm B off (+.10), consistent with the CPT parent adding some explicit
  translation ability.

## Findings

1. **Reading Turkish is the main gap, in both modes and for all models.** Understanding is the right target.
2. **The exp-016 SFT is mixed.** It raised Belebele Turkish by 10-13 points (human-translated, English unchanged) but lowered
   machine-translated math reading by about 12 points with thinking on and made Turkish replies with thinking off much worse
   (cell B: base .77, arm A .58, arm B .52). The two measures disagree, so one benchmark alone must not drive the next design.
3. **Arm B (CPT parent) beats arm A on Belebele** (+3.4 points Turkish) and has the best translate-first score, but is the
   worst on Turkish-reply math with thinking off and replies in English to Turkish e-mail prompts. A reply-language
   failure like that was not visible in any earlier metric.
4. **Restating the problem in English first adds nothing** over reading it directly once the reply is English
   (F vs C for the base: -.01 thinking on, +.00 off). Drop it as a training target.
5. **The CPT adapter alone is not usable** (no EOS in 70% of writing answers, Belebele Turkish at chance), as in the earlier
   baselines. Its Belebele number is partly a format effect and not a clean measure of comprehension.
6. **The automatic unknown-word rate does not separate the models** at this sample size: non-English candidates are at or
   below the human-text rate for A and B. It misses the semantic oddities seen earlier ("okuyacak mesafe"). The AI ratings
   below do rank them (B above A and base), but they are one AI rater, not a native speaker.

## Limits

One training seed per arm; machine-translated math items (about 4 of 26 inspected failures had translation flaws); one
greedy translation per item for cell G; the constraint check covers only 12 prompts; the writing sheet has not been rated
by a native speaker (only by an AI that had seen the aggregate results); arm A is exploratory. Belebele passage text is CC-BY-SA and kept out of Git.

## Regressions

No model was changed, so no regression in this experiment. The regressions of the exp-016 arms that this experiment exposes
are listed under Findings (2, 3).

## Writing review (AI assessment, not a human review)

The 160 answers (40 prompts x 4 anonymous models) were rated 1-5 with notes on vocabulary by **OpenAI Codex (GPT-6-based
assistant; runtime revision and settings unavailable)** on 2026-11-22 (`writing-review/review-ratings.json`, protocol at
the top of `writing-review/review-sheet.md`). The assessor did not open `review-key.json`, but it had read this README's
aggregate results first, so it was blind to model identity only in the sense of not seeing the key; its ratings may be
influenced by those aggregates (for example the English-reply failures of arm B). It is one rater, not a native speaker, and
its scale was not calibrated against a human. The summary below comes from `scripts/evaluation/summarize_lfm3_writing_review.py`
(coverage verified: 160 distinct ratings, 40 prompts, all answer text in the sheet identical to the generated answers;
`writing-review/review-summary.json`). Treat it as exploratory.

| Model | mean rating (1-5) | rated 1-2 | rated 4-5 | answers with vocabulary flags |
|---|---:|---:|---:|---:|
| base | 1.82 | 88% | 5% | 33 / 40 |
| CPT merged | 1.05 | 100% | 0% | 10 / 40 |
| arm A | 1.88 | 85% | 0% | 30 / 40 |
| arm B | 2.35 | 60% | 10% | 14 / 40 |

Paired by prompt (mean rating difference, 95% bootstrap interval): arm B - base +0.53 [+0.18,+0.85]; arm B - arm A +0.48
[+0.20,+0.78]; arm A - base +0.05 [-0.28,+0.35]; CPT - base -0.78 [-1.05,-0.50]. By category arm B is highest in
summaries (2.83), translation (3.0) and constraint prompts (2.67) and lowest in e-mails (1.67, English replies) and
explanations (2.0). Constraint prompts are few (12) and not analyzed separately.

Reading: on this rater's scale all four models write poor Turkish (even arm B averages 2.35, between "partly decipherable
with major problems" and "understandable but clearly non-native"). Arm B is the best, arm A is no better than the base, and
the CPT adapter alone is unusable in chat. The six answers rated 4 or 5 are arm B (wr-tr-18, 22, 31, 40) and base (wr-tr-22,
23); a human should check those and a sample of the 1s before the ranking is relied on.

A second reading of the six top-rated answers by the same assessor found that the single score mixes Turkish naturalness
with task success: arm B wr-tr-18 got a 4 although it copies the source and exceeds the 30-word limit, and wr-tr-31 got a 4
although "en büyük kentidir" (Ankara) is false. Rank the models only after scoring naturalness and task correctness
separately (planned for the next review). The saved ratings were not changed.

## Owner's qualitative assessment (native speaker, 2026-11-22, from the AI summary and its excerpts, not a re-rating)

Grammar is generally good: not perfect, but passable for a model of this size, and clearly improved over the base model;
still not better than Qwen3.5-4B. The slips look like human errors rather than nonsense: "artıran" for "arttıran",
an unnecessary suffix ("taze meyveleri kokar" for "taze meyveler kokar"). The more serious failure is hallucinated
vocabulary, for example translating "meeting" as "meydan okuma" instead of "toplantı". Checked against the key: "artıran"
came from the CPT adapter alone (wr-tr-02), "taze meyveleri kokar" from arm A (wr-tr-25), and "meydan okuma" from the base
and arm A (wr-tr-39); arm B did not make these particular errors, but it left that translation prompt in English.
The owner expects that teaching Turkish understanding will also improve Turkish writing.

## Conclusion

The gap is mainly reading Turkish (22 points with thinking on, 35 to 46 with thinking off), not arithmetic and not writing
when the reasoning happens in the English think block. The exp-016 SFT is mixed: Belebele Turkish +10 to +13 points,
Turkish math reading about -12 points with thinking on, Turkish-reply math with thinking off much worse, and arm B answers
some Turkish prompts in English. Neither translate-first nor restate-first is a usable no-training fix. The unknown-word
rate cannot rank these models; the AI ratings do (arm B best, arm A about equal to the base, CPT alone unusable), and the owner's read agrees that
the Turkish is passable for the size, with mistranslation (hallucinated word meanings) the most serious remaining defect.

## Next step (proposed, not run)

A training design that (1) uses Turkish prompts whose targets are the model's own full reasoning on the English version,
(2) keeps the reply language Turkish and carries the reasoning in thinking-off replies, (3) includes e-mail, translation
and other writing prompts so reply language does not drift, and (4) is gated on Belebele, Turkish math, tool calls, the
writing probe and an English guard set together. It needs about 3k Turkish prompts with faithful English twins (the owner
is arranging the translation); parallel text for comprehension is the alternative if rule 4 is taken literally.
