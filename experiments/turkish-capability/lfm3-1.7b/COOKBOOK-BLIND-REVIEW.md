# Cookbook blind review, 2026-11-20

All 34 records have exactly one submitted judgment and valid rankings with ties.
Source inference hashes were verified; model identities were decoded per record.
Raw API snapshots remain in ignored `cookbook-runtime-local/argilla/`; decoded
reviews and summary are in `COOKBOOK-BLIND-REVIEW.json`. Submissions are unchanged.
User-reported AI-assisted judgments measure preference, not absolute accuracy.

| Left model vs right model | All 34 W/T/L | OFF, 26 W/T/L | ON, 8 W/T/L |
|---|---:|---:|---:|
| Exp014 vs base | 16/2/16 | 14/1/11 | 2/1/5 |
| Exp015 vs base | 17/1/16 | 14/0/12 | 3/1/4 |
| Exp014 vs exp015 | 14/8/12 | 12/5/9 | 2/3/3 |

TR→TR OFF: exp014 vs base 6/1/6; exp015 vs base 8/0/5 (13 records).
EN→TR OFF: exp014 vs base 8/0/5; exp015 vs base 6/0/7 (13 records).
There is no consistent overall winner. SFT sometimes improves brevity, Turkish
output compliance and naturalness, but still reverses meaning, omits constraints,
invents words and contradicts calculations. Several wins are among all-wrong
answers. Reliable Turkish capability transfer is not established.

Thinking does not resolve Turkish word-problem comprehension: base is preferred
on that slice. Symbolic ON scores (8/8 for all models) are a separate measure.
Exp015's verified missing thinking closure on all eight Turkish word problems
remains a structural regression, regardless of preference rankings.

## Note corrections verified after re-export

Compared by stable record ID, exactly four notes changed: ticket-change EN→TR
OFF, and session-end-time, average-target and egg-boxes TR→TR ON. All 34 rankings,
model mappings and aggregate results are unchanged. The unrelated announcement
record is identical to the previous export. Previous decoded data and raw API
snapshots are retained locally; `COOKBOOK-REVIEW-NOTE-CORRECTIONS.json` records
the changed IDs and previous/current snapshot hashes.

The ticket note now correctly accepts both equivalent arithmetic expressions;
its ranking rests on explanation quality. The three ON notes now evaluate final
answers without penalizing English internal reasoning. These four issues are
resolved in the current notes, rather than pending corrections.

## Remaining judge limitations and next action

- Evaluate final-answer language separately from internal reasoning throughout
  any subsequent correctness audit.
- The discount ON note claims base closure is not visible, but the raw-output
  audit finds base closes all 16 ON outputs. Trust raw evidence for closure.
- Correct intermediate numbers do not make contradictory final answers correct.

Next: adjudicate the eight ON word problems and the remaining closure inconsistency from
raw answers, recording correctness, final-answer Turkish and closure separately.
Then compare existing matched English-direction outputs to distinguish Turkish
comprehension failures from arithmetic failures. No GPU needed for this analysis.
Do not launch another training run solely from near-tied preferences. Repeated
directions/modes are correlated and these are consumed development tasks, not a
fresh final holdout. No submissions were changed during this export.
