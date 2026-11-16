# Pilot80 output review

## Local Argilla review queue

[Open the 20-prompt blind comparison](http://127.0.0.1:6900/dataset/27f59ab3-0b15-40a2-a36a-efe218e15155/annotation-mode).
Owner simplified the review protocol before grading: only rank A/B/C from best
to worst (ties allowed) and write a free-text explanation. No per-dimension labels
are required. All20 prompts and all three complete answers remain unchanged;
identities change per prompt, with6 or7 appearances in each position. Submit each
record. State all-bad cases or uncertainty in the explanation.

Summarize paired preferences and ties from these rankings, with qualitative error
analysis from notes. The former correctness/instruction pass counts cannot be
reported as directly human-annotated metrics under this simpler protocol. The
detailed criteria below are interpretive guidance only, not required form fields.

The former detailed queue remains intact to preserve any saved work. Use the new
simple queue linked above. Its record-specific identity key is kept only under
ignored `pilot80-runtime-local/argilla-blind-review-simple-v01/`. Decode only after
grading; do not use the offline page's fixed-column key or the older queue key.
Neither identities nor automatic scores are uploaded to the UI.
The creation script verifies all full response texts after upload and safely
reuses matching records without overwriting responses:
`scripts/evaluation/publish_lfm3_pilot80_blind_argilla.py`.

## Grading criteria

Review the20 held-out prompts after both predeclared SFT checkpoints complete.
Use `pilot80-runtime-local/blind-review.json`; keep the separate column mapping
hidden until grading is finished. Review complete outputs, including failures.
No grades select a checkpoint or change this pilot's recipes.

For each prompt/answer, record:

| Field | Values | Interpretation |
|---|---|---|
| Correctness | pass / fail / uncertain | Claims, calculations and grounded conclusions follow the question and available evidence. |
| Instruction following | pass / fail / uncertain | Requested format, constraints and actual task are satisfied. |
| Turkish | good / needs edit / poor | Natural, grammatical Turkish; retain required foreign terms or source strings. |
| Detail | appropriate / too short / too long | Judge against what this specific task needs, not a universal length target. |
| Repetition or drift | absent / present | Repeated content, irrelevant continuation or loss of task focus. |
| Notes | free text | State the concrete error or uncertainty and any reference issue. |

The primary descriptive result is a pass count out of20: correctness and
instruction following both pass. Keep uncertain judgments separate and report
paired item outcomes. Do not treat reference exact match as semantic correctness.
Reference answers are reviewed anchors, not exhaustive or infallible gold text.
Flag a questionable reference consistently for all three candidate answers.

Simple direct answers do not require thinking tags or extra explanations. Reward
useful reasoning when the task calls for it; avoid rewarding length alone. A
correct first sentence followed by looping, contradictory or irrelevant material
is not automatically a successful complete answer. An appropriate long answer
should not fail merely for being long.

Keep generation termination, token length and lexical repetition as supporting
measurements rather than substitutes for correctness. Compare CETVEL100 task
metrics separately, and retain TurBLiMP grammar accuracy as a regression check.
The repeatedly inspected CETVEL cohort and tiny source-balanced holdout support
pilot observations, not broad Turkish capability or release-quality claims.

After reviewing, identify missing or weak task families for the next independently
reviewed training batch. Do not move these20 prompts, their answers, or variants
into training. Create separate development data before further hyperparameter
selection; retain reusable general coverage as the main dataset objective.
