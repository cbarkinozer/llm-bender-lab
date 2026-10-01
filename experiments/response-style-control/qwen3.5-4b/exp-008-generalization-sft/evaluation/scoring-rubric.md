# Frozen development comparison protocol

Evaluate all 50 exp-007 reviewed-v2 questions using the config-pinned model,
thinking disabled, greedy decoding and 256 maximum new tokens. Generate the
base before training; compare with the final scheduled three-epoch adapter.
Do not choose checkpoints using these outputs for this first run.

Randomize A/B identities per question with seed 3407 and keep the mapping
private until human annotations are exported. For each answer, record task
completion and correctness first, then natural/coherent Turkish and whether
the item's pass condition is met. Equivalent valid wording is acceptable.
Shortness is not a substitute for correctness. Lists and longer explanations
are acceptable where required by the question.

Record applicable failures: unnecessary clarification, unsupported fact or
cause, lost qualification, invented self-state, language/meaning error,
contradiction, repetition, or incomplete answer. Record A/B/tie preference
separately from correctness. Report counts and per-item failures for each
10-question family, including ties and regressions.

The benchmark is development material informed by historical failures and user
review. Results support internal iteration; they do not establish broad Turkish
quality or general-capability retention. Independent evaluation must be frozen
before making broader claims. Training-data composition and total training
volume both differ from exp-006, so causal attribution to curation alone is not justified.
