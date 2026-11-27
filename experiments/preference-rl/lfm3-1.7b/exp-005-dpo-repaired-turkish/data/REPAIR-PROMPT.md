# Repair prompt for the rest packet (exp-005)

The context message given to the repair assistant for the 1,700 rest items. The task rules live in `REPAIR-GUIDE.md`; this message adds the job
setup and what the pilot taught. Paste it as is.

---

You are repairing Turkish answers for a preference-learning dataset (repo `llm-bender-lab`, experiment `exp-005-dpo-repaired-turkish`). A small
Turkish language model answered prompts that carry their own data (summaries, extractions, lists under limits). Each answer is repaired by you; the
repaired answer becomes the preferred side of a training pair and the model's own answer the rejected side, so the two must differ only where the
original is wrong. Bad "repairs" teach the model wrong things, so quality matters more than speed or yield.

**Read first:** `experiments/preference-rl/lfm3-1.7b/exp-005-dpo-repaired-turkish/data/REPAIR-GUIDE.md` (rules, verdicts, output format, two worked
examples). It is the source of truth. Do not read `results-local/repair-output-pilot*.jsonl` or other earlier outputs to copy from.

**Files** (all under `exp-005-dpo-repaired-turkish/results-local/`): six input parts `repair-input-rest-part1.jsonl` ... `part6.jsonl` (284, 284,
284, 284, 284, 280 rows, 1,700 in total). Work part by part. For each part write `repair-output-rest-partN.jsonl`: exactly one JSON object per
input row, same `id`, same order, format `{"id", "verdict", "chosen", "changes"}` as in the guide.

**What the pilot showed (300 items, the same kind of rows):**
- About half of the answers could be repaired (about 31% `larger`, 20% `minimal`), 47% ended as `rewrite_needed` and 2% as `none`. These
  numbers are for calibration only. Do not aim for a quota; judge every row on its own.
- Many answers are mostly invented content (facts, causes, numbers or recommendations that the prompt's data does not contain). Say
  `rewrite_needed` with a short reason instead of inventing content to fill the gap. Never pad to reach a word count; restating data that is in
  the prompt is allowed when a stated minimum needs it.
- The allowed range is 50%-110% of the original's words (`repaired_word_range` in each row). Removing invented content may shorten the answer;
  that is fine. Concise answers are wanted, as long as nothing the prompt requires is dropped.
- Cover every target the prompt names. When it asks for N items, give N concrete items made from the data, not a filler item.
- Code checks every repair afterwards: unknown or English words (real Turkish words with correct diacritics only; names and terms from the prompt
  stay as they are), countable limits (words, sentences, bullets, exact N, required words), decimal numbers and `1.` / `-` list markers are fine,
  and the answer must end like a finished answer (a JSON answer may end in `}`).

**Before you save each part, check yourself** with a small script, not by eye: all ids present once and in input order; valid JSON on every
line; `chosen` empty only for `none` and `rewrite_needed`; every non-empty `chosen` inside `repaired_word_range`; countable limits met (count
words, sentences, bullets); `changes` present for `minimal` and `larger`.

**Also write** `repair-output-rest-partN.provenance.json` next to each output (task, model family and revision if known, date, guide sha256,
input and output sha256, item count, verdict counts, the checks you ran). These files stay local and are never committed.

When a part is done, report: rows, verdict counts, how many rows you spent most time on and why. Do not run training, do not touch other
files, do not commit. After all six parts, say so; the next step (code validation and a retry pass for failures) is done by the owner's tooling.
