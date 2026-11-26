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
