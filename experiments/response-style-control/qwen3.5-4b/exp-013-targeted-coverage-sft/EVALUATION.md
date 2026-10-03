# Pre-run C/D development comparison

C vs saved A: narrower12-row intervention. D vs C: longer cosine recipe on
EXACT same approved80 targets; four/40 vs six/60 epochs/steps. A/C/D all start
independently from the pinned instruct model. Never continue a previous adapter.

Final scheduled adapters are preselected; do not select a checkpoint by minimum
development loss or shortness. Dataset approval and all required GPU checks must
precede training. No new GPU has been requested or assumed alive.

## Fixed generation

Same20 reviewed-v2 development inputs, pinned tokenizer/template, thinking off,
no extra system prompt, greedy BF16 HF/Unsloth, repetition penalty1.05,
batch1, seed3407,4096-token budget; same bounded runner with exact-token-loop
and180-second guards. Preserve native EOS / length / repetition / time stop
reason, raw output, prompt IDs/hash, output token counts and final-answer status.
Non-EOS stops are incomplete failures, not hidden reruns. Any recovery rerun
gets a separate version with its predecessor preserved. Reuse saved A only
after strict item/template/prompt/settings parity checks. Historical base was
vLLM; do not claim exact backend parity if showing it as extra context.

## What to judge

Argilla desired/A/C/D: task substance pass/partial/fail per arm, preference
including tie/neither, optional issue labels and notes. Correct task completion,
grounded reasoning, uncertainty preservation, natural Turkish and selective
clarification precede style. Exact answer-only constraints are substantive;
unrequested formatting is also tracked separately. Shortness is not accuracy.

Report all20 per-item judgments and aggregate counts with denominators; also
the predeclared eight high-signal items049/050/059/069/070/079/089/090.
Preserve failures on009/010/049, wins/regressions on029/030/070/079/090/099,
without training their scenario paraphrases.

me-089's assistant QA reference is disputed. Display its provenance clearly,
retain frozen reference/results, and report sensitivity without089 (19items;
seven anchors). A revised reference must be separately approved/versioned,
applied consistently to all arms and never overwrite the old evaluation.

## Decision rule and limitations

Advance a candidate only if review shows a useful substantive gain and no
unacceptable trade-off in natural Turkish, necessary explanation, interaction
or stopping. Inspect each new failure rather than letting preference hide it.
If D merely shortens outputs, loses conditions or repeats generic advice,
do not call longer training better. If neither improves, retain A as the working
comparison and record a negative result. No universal automated numerical
promotion threshold or statistical significance is claimed for one reviewer20items.

This is development, single seed and non-blind review. No independent final
accuracy, global reasoning preservation, no-hallucination or no-forgetting claim.
Separate thinking-mode/training-fit probes may be retained as diagnostics but
must not be counted as additional independent primary test items.
Independent final test and retention checks remain needed for a success claim.
