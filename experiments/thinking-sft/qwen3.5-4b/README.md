> Deferred — 2026-10-31: preserve this Occam2/Turkish infrastructure and data for
> later. The active demo is [whole-app requirements-to-tests thinking SFT](../../unit-test-generation/qwen3.5-4b/exp-001-local-thinking-10/app-core-v04/README.md).
> The older active-priority text below describes the earlier plan.

# Occam 2 — Turkish Thinking SFT on Qwen3.5-4B

Active learning pilot, 2026-10-28. Supersedes the unit-test/TDD project as the
immediate priority. Start from untouched `Qwen/Qwen3.5-4B`, not Occam or Reflex.

## Objective

2026-10-29 priority: [failure-guided data revision](FAILURE-GUIDED-REVISION.md).
The generic80/20 draft below is preserved for infrastructure checks. It is not
the selected final dataset. Diagnose historical failures and successful controls
before choosing revised reasoning examples. Full training and held-out baseline
are gated until that revised selection is ready.

Learn reasoning-inclusive supervised fine-tuning while improving a useful,
checkable narrow task. Prepare exactly 80 training cases and 20 held-out cases.
The task is Turkish document-grounded reasoning with concise Turkish answers.
Both Turkish worked reasoning and final answers receive supervision. Turkish
reasoning output and answer accuracy are separate measured outcomes; neither
improvement nor an internal language of computation is assumed.
The80/20 authored draft, native-label audit and runnable scripts are prepared.
No actual4B training or held-out baseline result exists yet.
An 80-example pilot tests specialization, not acquisition of general reasoning.

## Experiments

- `exp-000-baseline`: untouched-model evaluation; planned, not run.
- `exp-001-thinking-sft`: one BF16 LoRA recipe; planned, not run.

## Data and evaluation contract

- Author explicit problem statements, short worked solutions, and final answers.
  Worked solutions are constructed teaching material, not claims about a model's
  private reasoning or access to another service's hidden reasoning.
- Store `reasoning_content` and final `content` separately. Apply the pinned
  native template once; do not insert a second pair of thinking delimiters.
- Give reasoning, final answer, and end-of-turn tokens training loss; mask user,
  system, and padding tokens. Decode actual labels to verify this before training.
- Freeze train/test groups before authoring close variants. Keep the 20 tests
  out of training, smoke, tiny-overfit checks, checkpoint selection, and tuning.
- Use training-only diagnostics for this small pilot; preselect the final update
  count. The requested 20 are test cases, not a validation split.
- Compare untouched model and adapter with thinking explicitly enabled, identical
  prompts, backend, sampling, and total output budget including reasoning.
- Score final correctness/constraint satisfaction as primary, plus format,
  termination, tokens, latency, and a short manual reasoning-consistency review.
  Longer output or more `<think>` tokens is not evidence of improved reasoning.
- Preserve the baseline outputs before training. Report raw paired wins/losses
  and scores out of 20; this is small-pilot evidence with limited generalization.
- Freeze any simple general instruction-following regression probes separately;
  they are evaluation-only and do not increase the 80 training examples.

## Starting recipe (proposal)

BF16 LoRA, rank/alpha 16, dropout 0, learning rate 1e-4, effective batch 8,
three epochs / 30 optimizer steps for 80 examples on one GPU; seed 3407.
Packing off. Text-only training, vision frozen. Candidate projections:
q/k/v/o and gate/up/down, after inspecting the actual hybrid architecture.
Sequence length is selected after measuring the data, not copied from a notebook.
Pin the working environment on the chosen training host; no GPU rental or
training has been launched. Smoke and tiny-overfit checks remain required.

## Research

See [cookbook notes](COOKBOOK-NOTES.md) for sources and model/template identity.
See [Occam 2 execution plan](OCCAM2-PLAN.md).
See [RUN.md](RUN.md) and [Colab notebook](Occam2-Thinking-SFT.ipynb).
Next: complete the [original benchmark matrix](ORIGINAL-BENCHMARK-MATRIX.md),
review fixes/regressions, then finalize failure-guided training data and the
starting checkpoint. The matched local Q4 comparison remains separate from
historical native BF16 results and the earlier generic development probes.

Current execution update: the original128 outputs are complete. The uniform16k
greedy rerun was interrupted after clear repetition loops. Bounded sampler and
penalty diagnostics are now underway; see [inference diagnosis](INFERENCE-DIAGNOSIS.md).
No full benchmark restart or SFT run until the inference setup is validated.
