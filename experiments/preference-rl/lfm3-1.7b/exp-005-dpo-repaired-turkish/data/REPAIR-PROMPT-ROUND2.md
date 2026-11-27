# Repair prompt, round 2 (exp-005)

The context message for the second round: 32 retry rows and 150 second-sample rows. Same job and rules as `REPAIR-PROMPT.md`; paste it as is.

---

Round 2 of the repair job (repo `llm-bender-lab`, experiment `exp-005-dpo-repaired-turkish`). The six parts are done and validated by code: 1,075 usable
repairs, 983 training pairs after the brevity guard, a little under the 1,000 the experiment needs. This round closes the gap. The task, the rules and the
output format are the ones in `experiments/preference-rl/lfm3-1.7b/exp-005-dpo-repaired-turkish/data/REPAIR-GUIDE.md` (read it again, including
"Second pass (retry rows)"). Quality still matters more than yield: never invent or pad content to make a row usable.

**Two input files** under `exp-005-dpo-repaired-turkish/results-local/`, two output files, same format as before (`{"id", "verdict", "chosen", "changes"}`,
one object per input row, same `id`, same order):

1. `repair-input-retry.jsonl` (32 rows) to `repair-output-retry.jsonl`. Every row has `retry: check_failed`. Your earlier repair is in `previous_chosen` and
   `failure_reasons` lists what the code found (unknown or English words, an ending that looks cut). Fix exactly those, keep everything else, return the
   complete repaired answer. Words must be real Turkish words with correct diacritics; names and terms from the prompt stay as they are.
2. `repair-input-alt.jsonl` (150 rows) to `repair-output-alt.jsonl`. New rows: the earlier answer of these prompts gave no usable repair, so a **different
   answer of the same model to the same prompt** is given now. Treat each row as new and judge it on its own; `rewrite_needed` with a short reason is
   the right verdict when the answer is mostly invented. About half of such rows ended usable before, so no quota. The answers are short (median about 52
   words), so mind the `repaired_word_range` in every row.

Same self-check script as before, before saving each file (ids once and in order, valid JSON, `chosen` empty only for `none` and `rewrite_needed`, inside
`repaired_word_range`, countable limits met, `changes` present for `minimal` and `larger`). Write `repair-output-retry.provenance.json` and
`repair-output-alt.provenance.json` next to the outputs (task, model family and revision if known, date, guide sha256, input and output sha256, item
count, verdict counts, checks run). Do not read earlier outputs to copy from, do not run training, do not touch other files, do not commit.

Report per file: rows, verdict counts, how many rows took most time and why.
