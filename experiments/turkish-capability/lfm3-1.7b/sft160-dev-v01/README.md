# Pilot160 development protocol

Frozen before new-model inference:20 independently agent-authored examples, four
each in editing, grounding/clarification, exact constraints, reasoning and natural
Turkish. No training updates may use these rows or references. Original20 remain
diagnostic only. This small development set is not a release benchmark or an
owner-adjudicated dataset. Reference wording is illustrative except exact-output
tasks. Categories share intended skills with training, not copied source items.

The primary comparison disables thinking and uses matched vLLM BF16,8192 context,
4096 generated-token budget, temperature0.1, top-k50, top-p1, repetition penalty1.1,
seed3407, explicit native EOT and the historical loop guard. All four checkpoints
receive identical prompts. Untouched pinned LiquidAI is generated before SFT.

For each response, grade task correctness and requested constraints together as
pass/fail using the row rubric. Separately grade Turkish naturalness pass/fail:
no malformed morphology, unnatural word combinations or meaning-distorting syntax.
Equivalent correct answers are accepted; do not rely on whole-answer exact match.
Report both20-item counts and each four-item category; keep notes for every failure.

Selection order: exclude candidates with numerical/meaning hallucinations in more
than one dev item above the best candidate; then maximize task+constraint passes,
then natural-Turkish passes. A one-item difference is practically tied: prefer
epoch3; if duration ties, prefer the lower learning rate. These exploratory rules
do not establish statistical superiority. If all candidates are poor, select none.

Regression guardrails relative to untouched base: TurBLiMP overall accuracy must
not fall more than2 percentage points, nor any phenomenon more than5 points.
CETVEL100 is supporting development evidence: report task metrics separately;
flag any task decline over5 points (0–100 scaled task scores) for inspection rather
than averaging unrelated task metrics. Stop/loop/length failures must not increase
by more than one dev item versus base. A flagged regression blocks a release claim,
not the recording of an exploratory result. Freeze decisions before seeing outputs.

Optional separate reasoning4 probe evaluates the four reasoning prompts twice,
thinking off/on at the same4096 generated-token cap, for base and all four
checkpoints. Compare final correctness, rationale consistency, termination, total
tokens and latency. Preserve raw thinking; never mix these results into the primary
thinking-disabled selection count or claim equal computational work from equal caps.

Check lexical separation via `prepare_turkish_sft160_dev.py`: no normalized exact
prompt matches, no five-word containment≥0.35 and no shared12-word spans against
train160/old20. This does not certify semantic or cross-lingual independence.
