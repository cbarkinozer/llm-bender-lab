# Judge guide (exp-005)

Fixed on 2026-11-26, before any model answer for this experiment exists. The judge is a model of a different family than the repair model. It is
shown a Turkish prompt and two answers, A and B, in random order, and does not know which model wrote which. It never sees the detector or checker
results.

## Question

Which answer is better for the person who wrote the prompt? Decide in this order; the first criterion that separates the answers decides.

1. **Faithful to the prompt's data.** No claim that contradicts the data, reverses it, changes a number, or adds a fact, cause or recommendation the data
   does not contain. A short answer that is faithful beats a longer one that invents.
2. **Does the task and keeps every stated limit.** Count words, sentences, bullets and required parts yourself when the prompt states them. A broken limit
   or a missing required part loses to an answer that keeps it, unless the other answer breaks a limit of equal weight.
3. **Correct, natural Turkish.** Invented or misspelled words, missing diacritics, wrong suffixes, sentences that do not parse, English words that are not
   names or terms from the prompt lose.
4. **No padding or repetition.** The same statement twice, commentary about the answer itself, or a preface lose.

Do not prefer the longer or the shorter answer for its length, the more formal or friendlier tone for its tone, or the first or second position.
If both answers are equally good or equally bad on the deciding criterion, answer `tie`.

## Output (one JSON object per comparison)

```json
{"id": "...", "winner": "A", "deciding_criterion": 1, "note": "one short sentence"}
```

`winner` is `A`, `B` or `tie`. `deciding_criterion` is 1 to 4 (0 for a tie). The comparison table maps A and B back to the models after all
judgments are written; judgments are not edited afterwards.

## Procedure (added 2026-11-27, before any held-out answer exists; the criteria and the output format above are unchanged)

**Who judges.** An AI assistant of a different family than the repair model. That is a model's judgement, not an
independent human check, and the README says so. Rule 6 (the owner's own blind read of 30 comparisons) is the human check and is never replaced by it.

**Sets.** Each set has one comparison per held-out prompt (200), using the temperature-0.1 answers.

| set | pair | used for |
|-----|------|----------|
| A | `dpo-on-sft` against exp-021 | rule 1 |
| B | `dpo-on-sft` against `sft-only` | rule 2 |
| C | `sft-only` against exp-021 | only if rule 1 passes and rule 2 fails (it backs the sentence "SFT on repaired answers helps") |

Answers whose text is identical after whitespace normalisation are a tie by code, are not shown to the judge, and are reported separately (they are
not decisive).

**Blindness.** `scripts/evaluation/tr_dpo_judge.py sheets` builds the sheets and a key with a fixed seed; which system sits in position A is random per
item. The key is **not opened until every batch of the set has a saved judgment file**. The judge sees the prompt, answer A, answer B and the word
count of each. It does not see model names, the hypothesis, which answer is expected to win, the tallies so far, or other sets' judgments of the same
prompt. Batches of 25 items in a fixed random order; a saved batch is final (no revisions after a later batch or after the key is opened). The prompt
group (constraint, context, plain_source) is added only in the analysis.

**Working method per item.** Note what the prompt asks (task, data, hard limits), check each answer against criteria 1 to 4 in order, and read the
pair in the order B then A before deciding. `note` names the concrete difference ("B invents a 4 percent figure"), not an impression. `tie` means no
clear difference on the deciding criterion; it is not a way to skip hard items, because one answer with a data or limit error that the other lacks is
a decision. A longer answer wins only when it carries content the shorter one lacks and the prompt asked for it. An answer that stops mid-sentence
loses to a finished one under criterion 2. Missing diacritics count under criterion 3 only when the prompt itself uses diacritics.

**Analysis** (`tr_dpo_judge.py unblind`): per set the decisive comparisons, win share, Wilson 95% interval (z = 1.96), tie share, the split by prompt
group and by deciding criterion, and the share of `A` among decisive judgments (a value outside 40-60% is reported as a warning; decisions are not
changed). Rules 1 and 2 use the win share among decisive comparisons exactly as the README states them.
Because the training answers are short (mean 34 words against 68 for exp-021 on the held-out prompts, known before judging), the analysis also reports,
as a robustness split and not as a decision rule, how often the shorter answer wins and the win share among decisive comparisons whose two word counts
are within a factor of 0.75 to 1.33. This was added on 2026-11-27 after the held-out answers existed but before any judgment was made.

**Judge sanity check (before set A).** 30 random training pairs (chosen against rejected, order randomised, key kept apart) go through the same
procedure. This tests the procedure, not a model: the judge should prefer the repaired answer in at least 80% of the decisive items. If not, the
procedure is examined before any set is judged (the held-out answers are still unjudged at that point).
