# Next GPU session: baseline first, then two controlled arms

Current implementation update: Arm B arrays, exact mask audit, shared-baseline/
arm-specific gates and explicit token-normalized loss are now implemented.
Start with PAIRED-GPU-RUN.md and paired-preflight-v01. The older pending-work
checklist below is retained as history. Actual GPU/Unsloth and Docker checks
remain pending; no baseline or training run has occurred.

## Follow-up review: repetition and ablation accounting

- Keep reserved `slm_test_generation` apps/tests/requirements out of all current
  train/development/holdout/reference fixtures. Read-only scalar protocol
  inspection does not authorize using its examples as data.
- Confirmed study repetition mitigation: v2 launcher temperature0.0,
  repetition_penalty1.15; inference helpers default1.05 but launcher overrides.
  Helpers also have native/role-stop strings and wall-clock abort controls.
  These are configured mitigations, not proof loops were eliminated. Do not
  copy generic stop strings such as code fences into our file-output protocol.
- Recommended baseline pilot: greedy temperature0 plus repetition_penalty1.15
  as the historical starting point, checking valid repeated identifiers/assertions.
  This is a recommendation, **not yet a recipe revision**: saved v03 still uses1.0.
  Before measured baseline, freeze the chosen penalty in a new shared revision
  for base/A/B. If diagnostics require changing it, regenerate the common baseline
  and keep prior diagnostics; do not tune each adapter's decoding separately.
- Tag headroom failures as suspected repetitive/degenerate reasoning versus
  progressive reasoning that simply exceeded the cap. Finish_reason=length alone
  cannot distinguish them. Preserve raw outputs/token IDs and reviewer evidence;
  repetition heuristics are flags, not automatic correctness judgments.
- Temperature0.1 remains sampling; it can still repeat. Positive temperature
  does not inherently make experiments irreproducible: seeds, same runtime and
  deterministic scheduling matter. Greedy also lacks cross-runtime bitwise
  guarantees. Check the installed vLLM's documented reproducibility controls
  before changing scheduling; no unverified switch is applied locally.
- A/B manifests must report actual supervised tokens per epoch/step and rationale
  tokens removed. Verify actual token-loss normalization including accumulation
  under Unsloth/Trainer; do not merely assume default settings implement the
  desired normalization. Token-mean loss does not eliminate the different
  supervision objectives/exposure. Interpret results as direct rationale
  supervision holding input exposure equal, not an isolated proof about reasoning.

Saved2026-11-01 for the owner's next session. Repository checkpoint and artifacts
are sufficient to recover the plan; do not rely on chat memory.

## Owner's experiment preference

Amortize pod provisioning, model download, warmup and evaluation across two
experiments. Ask one useful controlled question, changing one factor between
arms; do not launch an arbitrary hyperparameter sweep. Baseline first, inspect
headroom/floor and runtime validity, then proceed with both arms if worthwhile.

Proposed question: does direct supervision of our short authored rationale help
requirement-to-pytest generation beyond supervising the test answer?

| Setting | Arm A | Arm B |
|---|---|---|
| Fresh base | Same pinned Qwen3.5-4B | Same, never initialized from A |
| Data/order/seed | Same50 train tasks, seed3407 | Identical |
| Input IDs and attention masks | Full existing conversations | Identical |
| Rationale-text loss | Supervised | Masked |
| Pytest answer and end-of-turn loss | Supervised | Supervised |
| LoRA/optimizer/LR/scheduler | Same existing recipe | Identical |
| Epochs/effective batch | 3 / 8 | Identical |
| Inference | Thinking on, shared8192 output cap | Identical |

Keep delimiters consistently supervised where token boundaries permit. Audit
tokens spanning rationale/markup boundaries; record the exact policy and affected
counts. Do not use a string-search completion mask or silently alter BPE boundaries.
Arm B is **rationale-loss-masked**, not rationale-removed: teacher-forced test
tokens still condition on the supplied rationale. This isolates direct rationale
supervision, not the total benefit of rationale-free training. Loss normalization
and supervised-token exposure differ; equal epochs mean equal input exposure,
not equal loss-token exposure. One seed per arm is a diagnostic, not a robust
effect estimate. Answer-without-rationale-input is a different future experiment.

## Readiness distinction: important

The A/B design is saved, but **Arm B arrays/mask audit/runner support are not yet
implemented**. Existing GPU runner is the rationale-supervised A recipe. Do not
launch it twice and label the second run B. Before renting:

1. Implement and audit B labels; prove only intended rationale-label positions
   differ, with input IDs, answer labels, EOS and padding preserved.
2. Create separately frozen A/B recipes and exposure manifests. Validate actual
   trainer batches independently. Same seed/data order, fresh base each time.
3. Update evidence matching: shared baseline/runtime identity must be keyed to
   common inference/data settings, while smoke/tiny/reload/masking gates must
   remain bound to the corresponding arm. Current runner requires identical full
   recipe hashes, so it must be extended deliberately to reuse one baseline
   across different training-loss recipes. Do not weaken all gate checks.
4. Prepare two-arm launch/review commands; preserve private pair mapping and use
   A-vs-base, B-vs-base and A-vs-B review with a shared frozen rubric.
5. Then request/accept pod access with a revised two-arm time allowance.

## Paper study and corrected token budgets

Fetched the latest default-branch commit from
https://github.com/Prof-it/slm_test_generation:
`380b7d362f49d43fd55af5b2f7e015d4fa651e97`.
Read-only clone: `C:/Users/barkin/Desktop/slm_test_generation`.

The launchers specify **8192 generated tokens**, and **16384 total context**:

- `step3_modelling/run_experiments.py`: lines171–174 and189–192.
- `step3_modelling/run_realworld_experiments_v2.py`: lines158–161 and178–181.
- `step3_modelling/run_real_world_experiments_inference.py`: lines115 and124;
  line29 lists Qwen3.5-4B with thinking enabled by default.

These are configured launcher ceilings, not proof every saved generation used
those limits. The helper defaults are4096; explicit launcher8192 overrides them.
`design.yaml`'s dataset-context budgets describe a different pipeline stage;
do not confuse them with effective generator arguments. Study launchers also
use repetition penalty1.15, up to4 sequences and480-second generation timeout.
We inspected the budget settings, not adopted every study setting: our repetition
penalty remains1.0 and single-sequence scheduling remains fixed across arms.

Owner is right that4096 total generated tokens can penalize thinking-heavy base
outputs. Updated current preparation: **demo-preflight-v03**.

| Limit | Current value | Why |
|---|---:|---|
| Training sequence | 3072 | Longest selected training sequence2873; unchanged |
| Generation output | 8192 | Shared ceiling for base/A/B, including thinking |
| Longest development prompt | 505 | Measured with pinned native template |
| Required prompt+output | 8697 | 505+8192 |
| Inference total context | 9216 | Round required length upward to1024-token multiple |

This retains the study's output allowance while using a smaller sufficient total
context for our nine current development requests. Runtime still checks every
prompt+output allowance. Future inputs may require a new context revision.
No automatic promotion to16384 output tokens: if baseline still truncates inside
thinking, review and revise the common budget before training/comparing adapters.
A cap is not a forced length. Training context and inference context are distinct.

## GPU sequence and limits

Read GPU-DEMO-REVIEW-REVISION.md for protected scoring, runtime lock and review
procedures, with the v03 budget updates in this note. Older v01/v02 protocols
remain preserved. Reuse the prepared correct-reference/mutant controls; run them
on Docker before trusting execution scores. No local Docker daemon is available.

Run shared base development generation once and inspect completion, correct
reference passes, curated fault detection and semantic quality. Then separate
fresh-base A/B training and same-runtime inference. Hide rationales during test
quality review; report completion separately, retain all-task denominators and
label completed-pair analysis as conditional. Record matching LoRA modules and
actual trainable parameter count. Holdout remains unopened until the final
protocol/arms are fixed. Never use implementation source in model text.

Unknown public-repository pretraining overlap, one development family and tiny
sample sizes remain explicit limitations. Extra seeds cannot fix family coverage.
Reserve at least a substantial session: the earlier45–90min single-arm cold-run
allowance is no longer a two-arm completion estimate. Two training arms alone
roughly20–40min using the prior rough estimate; setup, larger-budget generation,
executor checks, model reloads and review add unknown time. Measure baseline and
smoke throughput before promising a total. No GPU has been rented or run.
