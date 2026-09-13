# Turkish Capability — Qwen3.5-4B

## Target capability

Improve Turkish language understanding and generation while preserving the
starting model's instruction-following and general reasoning behavior.

## Starting model

- Repository: `Qwen/Qwen3.5-4B`
- Revision: `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`
- Type: post-trained multimodal model, evaluated with text-only inputs

## Evaluation suite

- Target: CETVEL, pinned by Git commit in the evaluation configuration
- Supporting: Turkish output quality and correct stopping, sampled manually
- Regression: instruction following and general reasoning, benchmark not yet selected

The target protocol is defined in
[`configs/evaluation/turkish-cetvel-v1.yaml`](../../../configs/evaluation/turkish-cetvel-v1.yaml).
It must be frozen after the baseline smoke test passes and before the full
baseline is run.

## Capability budget

| Capability | Requirement |
| --- | --- |
| CETVEL target score | Improve over `exp-000-baseline` |
| Instruction following | Maximum 2-point absolute regression |
| General reasoning | Maximum 5-point absolute regression |
| Invalid or non-terminating outputs | No increase |

The regression benchmarks and their scales must be selected before this budget
can be operationalized. The numeric limits must not be changed after seeing a
fine-tuned result.

## Planned training method

The first fine-tuning experiment will use text-only SFT with Unsloth and BF16
LoRA. It will not use 4-bit QLoRA: the supplied Unsloth Qwen3.5 guidance warns
that Qwen3.5 has higher-than-normal 4-bit quantization differences.

Planned invariants for `exp-001-lora` are therefore:

- Transformers v5 with exact package revisions recorded before the run;
- 16-bit model loading and BF16 LoRA where supported by the selected GPU;
- language layers enabled for fine-tuning;
- vision layers disabled because the target dataset is text-only;
- attention and MLP LoRA modules enabled;
- gradient checkpointing set to Unsloth's implementation;
- rank 16 and alpha 16 as the initial adapter configuration;
- a 2,048-token initial context length, increased only in a later experiment;
- no full run until smoke test and tiny-overfit checks pass.

Qwen3.5's custom Mamba Triton kernels may make the first compile/warm-up step
look unusually slow. Compile time and steady-state step time must be recorded
separately rather than diagnosing the warm-up as a training slowdown.

Reasoning-mode retention is a dataset decision, not a loader toggle. Before
dataset construction, the experiment must choose whether reasoning behavior is
part of the capability budget and then define the reasoning/direct-answer mix.

## Current selection

None. No training experiment may be selected before the baseline exists.

## Work plan

Track the end-to-end experiment in [`TODO.md`](./TODO.md). The current gate is
the untouched-model CETVEL baseline; dataset and training work remain blocked
until that baseline is complete.

## Experiment registry

| ID | Status | Main change | Target score | Notes |
| --- | --- | --- | ---: | --- |
| `exp-000-baseline` | planned | Untouched starting model | — | Compatibility smoke test required |
