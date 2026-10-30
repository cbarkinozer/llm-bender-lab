# Original Occam benchmark: four-condition matrix — 2026-10-29

## Current diagnostic: loops and sampled decoding

The uniform16k greedy run was stopped after18 completed attempts. Inspection
found pathological repetition: me079 repeated a need-context discussion61 times;
me090 repeated "Okay, I'll write it"78 times. These are not evidence that the
questions require16384 reasoning tokens. All outputs and interruption evidence
remain in fixed-thinking-16k-v1. The original128-attempt matrix is unchanged.

Historical temperature0/repetition1.05 was retained for protocol continuity,
but should have been checked for thinking-mode degeneration before expanding
the token allowance. Current Qwen3.5 guidance recommends sampled thinking for
general tasks: temperature1.0, top_p0.95, top_k20, min_p0, presence1.5,
repetition1.0. Source: https://huggingface.co/Qwen/Qwen3.5-4B#quickstart.
Greedy decoding is a plausible contributor, not yet an isolated proven cause.

`sampling_diagnostic.py` runs only me049/me079/me090 for base and Occam: six
outcome-selected attempts, not a new benchmark. Fixed output4096/context20480,
same prompts/seeds/artifacts. First condition uses the recommended sampler with
repetition1.0, saved in sampling-diagnostic-v1. The owner requested a modest
increase; a separate repetition1.10 condition is queued to run after the first,
saved in sampling-diagnostic-repeat110-v1. Other sampler settings remain equal.
The runs are sequential to avoid resource contention between loaded models.
Actual returned sampler settings are verified for the1.10 condition.

The original exact source for the in-progress repetition1.0 diagnostic is saved
beside its manifest. No previously saved condition is silently edited or replaced.
Do not launch another full benchmark until these bounded checks are inspected.
More repetition penalty may distort wording; it does not guarantee termination.

## Active update: uniform16k thinking rerun

Historical state: this run is now interrupted as described above, not active.

The owner superseded adaptive8k/16k recovery with one fixed setting for ALL64
thinking-on attempts. The adaptive process was stopped with zero completed
outputs; its interrupted manifest/logs remain in budget-recovery-v1.

Active runner: `fixed_thinking_matrix.py`; output directory:
`fixed-thinking-16k-v1/`, progress log `fixed-thinking-16k-v1.log`, under the same
external root below. Every thinking-on item gets output allowance16384,
context20480, prediction-time allowance1200seconds. Original prompt, model,
sampling, seed and repetition window are unchanged. Native EOS permits early
completion; no item-specific allowance or dynamic escalation is used.

Generation ETA at launch: approximately2–3hours on this Mac, based on the original
thinking runs' combined84minutes plus extra generation for formerly capped items.
This is an estimate, not a guaranteed upper bound. Accuracy review is separate.
Any still-limited output will remain flagged, not silently treated as complete.

Status/summary filenames retain compatibility with the earlier diagnostic runner:
`recovery-manifest.json` and `recovery-summary.json`. Their provenance explicitly
identifies the uniform64-item protocol. Original128 outputs and review-v1 remain.

When all64 new attempts complete, create a new review without overwriting v1:

```sh
python review_occam_matrix.py prepare --work /EXTERNAL/MATRIX/run-v3 \
  --recovery /EXTERNAL/MATRIX/fixed-thinking-16k-v1 \
  --output /EXTERNAL/MATRIX/review-v2-fixed16k
```

The remaining sections retain the original run and superseded recovery history.

Evaluate all original20 items and all12 later controls under base/Occam1 with
thinking off/on:128 original attempts. Report old20, controls12, full32 and the
me089 sensitivity separately. This is development/regression evidence; it does
not become a fresh holdout because outputs are regenerated.

## Identity and representation

The historical Occam base is `unsloth/Qwen3.5-4B` at
`3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636`. The released F adapter revision is
`1a8a07ff2a29f51a2b6a635a8c219191a7377996`.

The previously cached untouched Q4 GGUF and released Occam GGUF have different
tensor-type mixtures despite the same nominal Q4_K_M name. They cannot serve
as the clean matched pair for this matrix. A new base export was made from
verified original source shards using the same llama.cpp converter/quantizer
commit `7fe450e19305b828c199d602c23a8337aaa1f03b`, BF16 conversion with `--no-mtp`,
then `Q4_K_M 4`, matching the released Occam procedure.

`occam_matrix.py` verifies exact tensor-name/shape/quantization-type parity,
vocabulary/token-type equality and native-template equality before inference.
The released Occam GGUF must match its known SHA256. The actual base source
shard hashes were rechecked before conversion. All artifacts remain external.

This local Q4 matrix is a matched deployment comparison. Historical HF/Unsloth
BF16 scores remain separate; backend, quantization and native EOG handling differ.
Do not present the new results as exact numerical reproduction of those runs.

## Fixed protocol

- Original messages only, including the me059 multi-turn context; no new system instruction.
- Original references and pass/partial/fail correctness/usefulness rules unchanged.
- One model at a time; llama-server, Metal, batch/parallel1, context8192.
- All four arms: greedy temperature0, repetition1.05 over the context, output cap4096,
  seed3407, prediction timeout180 seconds. Only the native thinking flag changes
  within each model. Greedy preserves the historical protocol choice; do not
  generalize its outcome to an optimized sampled-thinking recipe.
- Native raw-completion endpoint; exact rendered inputs, response/token metadata,
  reasoning/final split and termination retained. Cache reuse disabled.
- Token/time-limit outputs and missing final answers retained; no outcome retries.
- Native EOG replaces the historical Python EOS/exact-loop implementation; record
  this runtime adaptation rather than claiming identical stopping semantics.

## Execution and recovery

External root:
`~/Documents/llm-bender-artifacts/occam2/original-benchmark-matrix-v1/`.

The active run was launched into `run-v3/`; live item progress is saved to
`execution-v3.log`. Inspect `run-v3/matrix-manifest.json` for complete/error state
and saved count. `mechanical-summary.json` is written at completion or failure.
Outputs are saved after every completed item; no unfinished matrix has an
accuracy score. The runner owns and shuts down only its dedicated model server.

Earlier infrastructure attempts are preserved: run-v1 rejected the negative
repetition-window alias with HTTP400 before any generation; run-v2 encountered
HTTP503 while the model was still loading. Run-v3 uses the equivalent explicit
8192-token window and waits through the startup readiness response. Both earlier
attempts saved zero model outputs; no scored answer was retried.

If interrupted, use explicit `--resume` with the identical script/settings/model
paths. Completed item IDs are skipped, not regenerated. Changed code/provenance
requires a separately named run with the infrastructure reason recorded.

## Review after all128 outputs exist

```sh
python review_occam_matrix.py prepare --work /EXTERNAL/MATRIX/run-v3 \
  --output /EXTERNAL/MATRIX/review-v1
# Review ratings.json; keep private-mapping.json hidden initially.
python review_occam_matrix.py summarize --review /EXTERNAL/MATRIX/review-v1
```

Each model condition occupies each A/B/C/D position8 times. Grade new final
answers independently using the existing rubric; old grades are not copied to
new generations. Inspect reasoning for changed answers, invented assumptions,
language and wasted work separately. Report fixes and regressions by item, not
only totals. Preserve original me089 rubric nuance and show exclusion sensitivity.
Human scoring remains pending until ratings are actually submitted.

## Higher-budget recovery — owner requested 2026-10-29

Original generation finished128/128. Base thinking-on had7 token-limit attempts;
Occam thinking-on had10. Both thinking-off arms naturally completed32/32; those
are termination counts, not correctness grades. Original outputs/review-v1 remain.

`recover_thinking_limits.py` reruns only those17 limited thinking attempts at8192
tokens/context12288/time600s, then only remaining token-limit attempts at16384
tokens/context20480/time1200s. Exact rendered prompts, weights, greedy sampling,
seed and repetition window stay fixed. No correctness-based retries. Input
truncation is forbidden. Any remaining capped/time-limited outputs are reported;
larger allowance does not guarantee natural completion.

External recovery folder: `budget-recovery-v1/`; live progress:
`budget-recovery-v1.log`, beside `run-v3/`. Inspect recovery-manifest.json for
completion/error state and recovery-summary.json for remaining limits. The script
owns and stops its dedicated server. Explicit unchanged-code resume is supported.

This is an adaptive budget diagnostic, not a fresh uniform8192/16384-token
benchmark or evidence that reasoning accuracy improved. Report original-budget
and recovered outcomes separately; do not silently replace old scores.

After recovery completes, create a separate updated blinded review:

```sh
python review_occam_matrix.py prepare --work /EXTERNAL/MATRIX/run-v3 \
  --recovery /EXTERNAL/MATRIX/budget-recovery-v1 \
  --output /EXTERNAL/MATRIX/review-v2-budget-recovery
```

Preserve any existing review-v1 annotations. Do not treat its truncated thinking
outputs as fully evaluated high-budget answers. The new file carries per-attempt
output allowances and retains unchanged non-limited responses.

Use the completed comparison to select failure families and decide base-versus-
Occam initialization for reasoning SFT. Do not train on these benchmark items or
close paraphrases. Do not promote the generic authored80/20 draft by default.
