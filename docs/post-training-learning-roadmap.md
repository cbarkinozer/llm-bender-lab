# Post-Training Learning Roadmap

## Goal

Build practical breadth across distinct post-training objectives and model
architectures before spending substantial compute on narrow optimization. Each
roadmap item starts with one small, controlled experiment whose purpose is to
teach the workflow and expose its characteristic failure modes.

This is a learning sequence, not a claim that every technique improves every
model. Negative results remain valid results.

## Operating contract

Every pilot must have:

- one primary hypothesis and one primary experimental change,
- a pinned base model, dataset, benchmark, code commit, and environment,
- an untouched base-model baseline under the same evaluation protocol,
- train/development/test separation and contamination checks,
- task metrics plus a common catastrophic-forgetting regression suite,
- representation, smoke, and tiny-overfit checks where the objective permits,
- retained per-item outputs, logs, hashes, runtime, VRAM, and cost,
- a short conclusion stating what was learned and whether to continue.

Do not turn a breadth pilot into a hyperparameter search. Use one defensible
recipe, finish the comparison, record the result, and move to the next family.

## Breadth phase

### 0. Supervised fine-tuning foundation — active

Finish the Qwen3.5-4B response-style SFT line through exp-006. Demonstrate the
target behavior on the sealed internal holdout and on a version-pinned external
benchmark not authored for this project. Publish the training artifact and its
provenance while keeping benchmark test items out of training.

Completion evidence: reproducible adapter, base-versus-SFT metrics, blind human
review, external benchmark result, regression analysis, and artifact hashes.

### 1. Common evaluation and catastrophic-forgetting suite

Freeze a compact suite used by every later pilot. It should cover the target
task plus relevant instruction following, language, reasoning, factual,
formatting, and safety/tool regressions. Measure the base model and exp-006
under identical conditions.

Primary question: what useful capabilities are lost when the target behavior
improves?

This is a cross-cutting gate, not a one-time checkbox. Every subsequent
experiment reports its delta against this suite.

### 2. Preference optimization

Reuse one frozen task, SFT checkpoint, prompt distribution, and preference
dataset. Start with one DPO pilot against the SFT model. After that controlled
baseline, run separate small experiments for SimPO, ORPO, and KTO rather than
changing algorithms and datasets together.

Primary question: does preference optimization improve the target behavior
beyond SFT without exploiting response length, formatting, or judge bias?

Completion evidence: SFT-versus-method paired evaluation, preference-data
schema validation, length analysis, and forgetting-suite deltas.

### 3. RL post-training with verifiable rewards

Choose a small task with an executable or otherwise deterministic verifier.
Run one GRPO/RLVR pilot from a frozen SFT checkpoint and compare it with the
same-compute SFT baseline. Keep reward correctness, reward hacking, pass rate,
KL/drift, output length, and failed rollouts visible.

Primary question: can verifiable RL improve task success rather than merely
optimize the reward implementation?

### 4. Native reasoning-token SFT

Select a model with an explicit native reasoning format. Fine-tune permitted
reasoning traces while separately controlling loss on reasoning and visible
answer regions. Compare answer-only SFT with reasoning-token SFT on the same
tasks and token budget.

Primary question: does training the native reasoning channel improve final
correctness enough to justify its latency and token cost?

Do not train on hidden traces obtained without permission, and do not invent a
generic chain-of-thought token format when the model already defines one.

### 5. Reasoning distillation versus reasoning RL

On one verifiable reasoning task, compare reasoning distillation and reasoning
RL from the same starting checkpoint, with matched data and compute budgets as
closely as practical. Keep this separate from generic thinking-token SFT.

Primary question: which objective transfers verified reasoning behavior more
efficiently and with fewer regressions?

### 6. Continued pretraining / domain-adaptive pretraining

Run a small CPT/DAPT experiment on a legally usable domain corpus, followed by
the same SFT recipe used by a no-CPT control. Measure domain perplexity/task
gain, instruction-following recovery after SFT, and forgetting.

Primary question: what does domain adaptation add before supervised
instruction tuning?

### 7. Knowledge distillation

Use one fixed teacher/student/task setup. Begin with response distillation;
then treat reasoning distillation and logit distillation as separate follow-up
experiments because their data, storage, and objectives differ.

Primary question: which teacher signal improves the small student beyond the
same amount of ordinary supervised data?

### 8. Tool-use / function-calling fine-tuning

Train a small model on explicit tool schemas, tool selection, typed arguments,
tool-result context, final answers, abstention, and unnecessary-tool negatives.
Evaluate exact schema validity and execution success, not just textual
similarity.

Primary question: can the model learn when to call a tool, how to call it, and
when not to call one?

### 9. Multilingual and cross-lingual transfer

Use Turkish and English with held-out tasks in both directions. Compare
monolingual tuning with a controlled bilingual mixture while tracking positive
transfer, interference, translation leakage, and language consistency.

Primary question: when does Turkish–English joint tuning transfer capability,
and when does it cause interference?

### 10. Quantization-aware adaptation and deployment

Hold task data and adapter design fixed while comparing BF16 LoRA with a
carefully matched 8-bit or 4-bit/QLoRA path. Evaluate adapter mode, merged
weights, and the actual quantized deployment artifact separately.

Primary question: which quality changes come from training quantization, merge
precision, and deployment quantization respectively?

### 11. Mixture-of-Experts fine-tuning

Choose a small open MoE model and begin with one conservative adapter recipe.
Then use separate architecture-specific ablations for router frozen versus
trainable and shared/expert module adaptation. Measure routing distribution,
expert load balance, throughput, task gain, and forgetting.

Primary question: which MoE components can be adapted safely without router or
expert collapse?

### 12. Multimodal / VLM fine-tuning

Use a compact image-text task and independently identify projector, vision
encoder, and language-backbone parameters. Start with projector-only tuning;
later unfreeze one additional component per experiment.

Primary question: where must adaptation occur for the target visual behavior,
and what text-only capability is lost?

### 13. Text-diffusion model fine-tuning

Fine-tune one open text-diffusion model using its native noising, masking, and
denoising objective. Compare quality, controllability, latency, iteration
count, and long-output coherence under a frozen sampling protocol.

Primary question: how does adaptation and evaluation differ from an
autoregressive language model?

Architecture-specific follow-ups vary one noise schedule, masking policy, or
sampling choice at a time.

### 14. Decision-model fine-tuning and calibration

Confirm the exact Laya/LAYA model and its state/action interface before
designing the experiment. Train on a small decision or trajectory task with an
explicit abstain action and asymmetric error costs. Evaluate action quality,
confidence calibration, selective accuracy, and out-of-distribution behavior.

Primary question: can the model improve decisions while knowing when evidence
is insufficient?

Calibration/confidence training is a first-class objective here, not an
afterthought inferred from generated prose.

## Shared comparison milestone

After the SFT, preference, and verifiable-RL pilots exist, run a controlled
comparison on the same task family:

```text
same base revision
same train/dev/test split
same evaluation protocol
same deployment format where possible
    -> SFT
    -> SFT + preference optimization
    -> SFT + verifiable RL
```

Match data and compute budgets where possible and report any mismatch. This
comparison must not recycle the final test set for method or checkpoint
selection.

## Depth phase

Only after the breadth pilots are complete, select the few families that
produced useful or surprising results. Apply, in order:

1. data-quality studies,
2. architecture/objective-specific ablations,
3. meaningful hyperparameter search,
4. multi-seed replication,
5. scaling studies across data, model size, and compute,
6. confidence intervals and paired statistical tests,
7. checkpoint merging or interpolation where technically appropriate,
8. stronger deployment and out-of-distribution evaluation,
9. a report or paper synthesizing supported and negative findings.

Hyperparameter search is deliberately after data-quality work: optimizing a
noisy or invalid task more efficiently does not create a useful result.

## Current position

The active item is **0. Supervised fine-tuning foundation**, specifically the
exp-006 GPU preflight, full training, sealed evaluation, and blind review. Do
not begin item 2 merely because training finishes; item 0 also requires the
external benchmark and regression evidence, and item 1 establishes the common
evaluation backbone for all later comparisons.
