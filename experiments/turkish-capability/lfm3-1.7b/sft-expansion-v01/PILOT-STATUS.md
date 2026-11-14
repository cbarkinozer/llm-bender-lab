# Pilot status — 2026-11-13

40 original synthetic training-only drafts are available in
`pilot-train-draft.jsonl`. `PILOT-REVIEW.txt` presents every input turn, proposed
target and required-fact rubric without shortening the content.

Composition: 20 summaries, 8 grounded QA, 6 translations, 4 instruction controls
and 2 corrections. This is the pilot budget, not the final mixture.

Contexts, targets and rubrics were authored by the same Codex agent in this
session. No external teacher API, public passage or benchmark transformation
was used. Human approval and independent semantic review have not occurred.
Do not treat the targets as independently validated ground truth.

Every scenario/source family is assigned to train. Do not derive development or
holdout paraphrases from these contexts. Topic reuse alone is allowed; concrete
scenarios and prompt templates require group-level review before expansion.

Checks cover structure, hashes, counts, nonempty targets, replacement characters,
JSON/bullet controls, unchanged correction and exact prompt overlap against both
Occam splits and CETVEL500. Lexical nearest neighbours are recorded for triage;
they are not semantic clearance. Raw token statistics use the pinned tokenizer
without chat tokens and do not represent supervised-token counts.

The current passages are short; the longest summary supplies a more detailed
paragraph, not a long document. Longer passages, wider linguistic variation and
independent evaluation families remain expansion requirements. Several summaries
preserve many details rather than compress aggressively; review this deliberately
against coverage and requested length before adding more examples.

Next: independent row-level content review, any corrections in the builder plus
regeneration, semantic overlap disposition, then grouped expansion and native
chat/loss-mask audits. No GPU run or expanded-dataset publication is ready.
