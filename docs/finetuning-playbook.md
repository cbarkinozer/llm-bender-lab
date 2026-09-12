# Fine-tuning Playbook

This document is the operational playbook for fine-tuning experiments in `llm-bender-lab`.

It does not explain fine-tuning theory from scratch. Its purpose is to answer practical questions:

* What should be checked before training?
* What should be monitored during training?
* What should be done when a run fails?
* How should unexpected behavior be diagnosed?
* When should data, configuration, model, or training method be changed?
* When is a regression acceptable?

For dataset construction rules, see `dataset-guide.md`.

For benchmark and evaluation rules, see `evaluation-guide.md`.

For experiment organization, see `experiment-guide.md`.

For reproducibility requirements, see `reproducibility.md`.

---

# 1. Core Principle

Treat fine-tuning as a controlled experiment, not as a one-shot training job.

```text
Goal
↓
Baseline
↓
Data Validation
↓
Training Configuration
↓
Smoke Test
↓
Tiny Overfit Test
↓
Full Training
↓
Evaluation
↓
Regression Analysis
↓
Diagnosis
↓
Next Experiment
```

Every run should test a clear hypothesis.

Avoid changing multiple major variables at once unless the experiment explicitly studies their interaction.

---

# 2. Before Training

Do not start a full training run until the following conditions are satisfied.

## 2.1 Define the target capability

State:

```text
What should improve?
How will improvement be measured?
What supporting capabilities must remain intact?
What regressions are acceptable?
```

Good:

```text
Improve Turkish instruction following.

Improve tool-call argument accuracy.

Improve Python unit-test generation.

Improve JSON schema compliance.
```

Bad:

```text
Make the model better.
```

---

## 2.2 Establish the baseline

Evaluate the untouched base model before training.

The baseline and fine-tuned evaluation should use the same:

```text
prompt format
chat template
generation configuration
benchmark version
evaluation code
```

Never fine-tune first and reconstruct the baseline later.

---

## 2.3 Validate the dataset

Before training:

* manually inspect random samples,
* verify conversation roles,
* check empty inputs and targets,
* check duplicates,
* check language consistency,
* verify train/validation/test separation,
* check benchmark leakage,
* inspect length distribution.

Detailed rules belong in `dataset-guide.md`.

---

## 2.4 Inspect the actual training representation

Correct raw text does not guarantee correct training data.

Inspect examples after:

```text
chat templating
tokenization
truncation
packing
label masking
```

Verify where relevant:

```text
input_ids
labels
attention_mask
```

Decode tokenized samples back to text when useful.

If assistant-only loss is used, confirm that the intended assistant response contributes to the loss.

Incorrect masking may leave very few tokens or no valid training tokens in a sample.

---

## 2.5 Check sequence length

Do not guess `max_seq_length`.

Measure:

```text
median
P90
P95
P99
maximum
```

Check how many samples will be truncated.

When truncation occurs, inspect which part is removed.

Do not silently remove important parts of the target response.

---

## 2.6 Decide whether packing is useful

Packing may improve throughput when many samples are short.

Do not enable it automatically.

Verify:

```text
sample boundaries
EOS handling
attention behavior
label masking
```

after packing.

---

# 3. Choose the Training Strategy

Use the simplest method that solves the problem.

```text
Need full model adaptation and enough compute?
→ Full fine-tuning

Need efficient specialization?
→ LoRA

Need lower VRAM usage?
→ QLoRA
```

For small single-GPU experiments, LoRA or QLoRA is usually a sensible starting point.

---

## 3.1 Choose LoRA target modules deliberately

Do not blindly copy `q_proj` and `v_proj` from an unrelated tutorial.

For QLoRA-style training, applying LoRA to all linear transformer layers is a common and supported strategy:

```python
target_modules="all-linear"
```

This is often a strong starting point when memory and training cost allow it.

However, do not treat `all-linear` as universally optimal.

Restrict target modules when:

```text
VRAM or compute is constrained
the architecture requires special handling
the experiment intentionally studies adapter placement
a known model-specific recipe performs better
```

For some architectures, especially MoE models, relevant trainable parameters may not be represented as ordinary `nn.Linear` modules. Inspect the model architecture rather than assuming module names.

Always record the selected target modules.

---

# 4. Build the First Configuration

The first configuration is a hypothesis, not a final answer.

Important parameters include:

```text
learning rate
effective batch size
training steps / epochs
sequence length
LoRA rank
LoRA alpha
LoRA dropout
target modules
warmup
weight decay
optimizer
scheduler
precision
gradient checkpointing
```

Avoid tuning everything simultaneously.

Prefer:

```text
Experiment A
LR = 2e-4
rank = 16

Experiment B
LR = 1e-4
rank = 16
```

instead of changing learning rate, rank, data, epochs, and prompt format together.

---

# 5. Effective Batch Size

Do not confuse micro batch size with effective batch size.

A useful approximation is:

```text
Effective Batch Size
=
Micro Batch Size
× Gradient Accumulation Steps
× Data-Parallel GPU Count
```

Example:

```text
micro batch = 2
gradient accumulation = 8
GPU count = 1

effective batch ≈ 16
```

Record effective batch size for every experiment.

---

# 6. Check Trainable Parameters

Before training, record:

```text
trainable parameter count
total parameter count
trainable percentage
```

IF trainable parameters are unexpectedly zero:

```text
→ STOP.
→ Check adapter creation, target modules and parameter freezing.
```

IF substantially more parameters are trainable than expected:

```text
→ STOP.
→ Verify the training method and adapter configuration.
```

Do not continue until the discrepancy is understood.

---

# 7. Smoke Test

Never start a long run before a smoke test.

Typical smoke test:

```text
50–200 samples
10–50 steps
```

The goal is not model quality.

The goal is pipeline validation.

Check:

```text
training starts
loss is finite
no NaN / Inf
VRAM usage is acceptable
evaluation runs
checkpoint saving works
logging works
model reload works
generation still works
```

IF any critical check fails:

```text
→ Do not start full training.
→ Diagnose the pipeline first.
```

---

# 8. Tiny Overfit Test

Use approximately:

```text
20–50 samples
```

and intentionally try to memorize them.

The goal is not generalization.

The goal is to verify that the training signal can reach the model.

For this diagnostic test, temporarily reduce regularization when useful:

```text
LoRA dropout = 0
weight decay = 0
```

IF the tiny overfit test FAILS:

```text
→ Check labels.
→ Check masking.
→ Check trainable parameters.
→ Check target modules.
→ Check learning rate.
→ Check optimizer.
→ Check gradient flow.
→ Check dataset formatting.
```

IF the tiny overfit test PASSES but full-dataset learning is poor:

```text
→ The basic training pipeline probably works.
→ Investigate data quality, task difficulty, optimization or model capacity.
```

Restore the real training configuration afterward.

---

# 9. OOM Debugging

First determine whether OOM occurs during:

```text
training
evaluation
generation
model loading
```

The correct response may differ.

---

## 9.1 Training OOM

Training memory roughly comes from:

```text
model weights
gradients
optimizer states
activations
temporary buffers
```

Try roughly in this order:

```text
1. Reduce micro batch size.
2. Reduce sequence length.
3. Enable gradient checkpointing.
4. Verify BF16 / FP16 configuration where appropriate.
5. Verify QLoRA / quantized loading if intended.
6. Use lower-memory optimizer states if optimizer memory is significant.
7. Reduce LoRA capacity or trainable scope if necessary.
```

Do not assume optimizer states are always the main problem.

In LoRA/QLoRA, long sequences and activations may dominate memory consumption.

Gradient checkpointing trades additional computation for lower activation memory.

---

## 9.2 Evaluation or generation OOM

IF OOM occurs during evaluation or generation:

```text
1. Reduce evaluation / generation batch size.
2. Ensure gradients are disabled.
3. Use torch.no_grad() or torch.inference_mode().
4. Check max_new_tokens.
5. Check whether unnecessary outputs are retained in memory.
6. Clear references to large tensors between batches when necessary.
```

If evaluation uses a serving engine such as vLLM or TGI:

```text
→ Check its GPU-memory allocation configuration.
→ Do not assume training memory settings apply directly to the serving engine.
```

---

# 10. During Training

Track both learning behavior and system behavior.

At minimum:

```text
training loss
validation loss when applicable
task metrics
learning rate
gradient norm
VRAM usage
GPU utilization
tokens/sec
steps/sec
```

---

# 11. Loss and Training Diagnostics

## 11.1 Training loss decreases

Usually expected.

It means:

```text
model is improving on the training objective
```

It does NOT prove:

```text
real task performance improved
```

Continue evaluating the actual target task.

---

## 11.2 Training loss does not decrease

IF loss stays flat:

```text
→ Run or revisit the tiny overfit test.
```

IF tiny overfit FAILS:

```text
→ Check labels.
→ Check masking.
→ Check trainable parameters.
→ Check target modules.
→ Check whether learning rate is too low.
→ Check gradient flow.
→ Check optimizer and dataset formatting.
```

IF tiny overfit PASSES:

```text
→ The basic pipeline works.
→ Inspect dataset complexity and quality.
→ Check whether learning rate is too conservative.
→ Check whether adapter capacity is sufficient.
→ Check whether the base model has enough capability for the task.
```

Do not immediately increase LoRA rank before ruling out data and optimization problems.

---

## 11.3 Loss suddenly spikes

Possible causes:

```text
learning rate too high
anomalous batch
very long sample
gradient instability
numerical instability
bad data
```

Inspect:

```text
batch contents
sequence lengths
gradient norm
learning rate at that step
raw samples
mixed-precision behavior
```

Do not automatically assume gradient clipping is the solution.

---

## 11.4 Loss starts unexpectedly low

Check:

```text
How many target tokens actually contribute to loss?
Is masking correct?
Is there data leakage?
Is the target duplicated in the input?
Is the task accidentally trivial?
```

A suspiciously low loss can indicate an incorrectly constructed training task.

---

## 11.5 Training improves while validation worsens

Likely overfitting.

Possible actions:

```text
fewer training steps
lower learning rate
better data diversity
more useful data
reduced adapter capacity
adjusted regularization
```

Diagnose before simply adding more data.

---

# 12. Training Is Slow

IF GPU utilization is low:

```text
→ Do not immediately blame the GPU.
```

Inspect:

```text
tokenization
CPU preprocessing
disk I/O
network storage
data loader
very small batches
evaluation frequency
checkpoint frequency
```

Track where useful:

```text
GPU utilization
CPU utilization
tokens/sec
data loading time
```

---

# 13. EOS, Repetition and Broken Generation

## Case — Model ignores EOS or generates endless repetition

Symptoms:

```text
response starts correctly but never stops
repeated phrases or loops
garbage after an otherwise correct answer
generation repeatedly reaches max_new_tokens
```

Check training data first:

```text
Are assistant targets terminated correctly?

Does the chat template append the expected EOS / end-of-turn token?

Was the terminating token truncated?

Were padding labels masked correctly?

Did packing alter sample boundaries?
```

Check tokenizer/model configuration:

```text
Is eos_token_id correct?

Is pad_token_id configured intentionally?

Does the model use more than one possible stop token?

Does the chat template use a special end-of-turn token instead of plain EOS?
```

Check generation configuration:

```text
Is the expected eos_token_id passed or inherited correctly?

Are required stop strings / stop token IDs configured?

Is max_new_tokens hiding a stopping problem?
```

Note:

`pad_token_id == eos_token_id` is not automatically an error. Some decoder-only models intentionally use EOS as padding. The important question is whether padding positions are handled correctly and excluded from loss where appropriate.

IF base model stops correctly but fine-tuned model does not:

```text
→ Compare pre- and post-training target formatting.
→ Inspect EOS/end-of-turn tokens in training labels.
→ Check truncation and packing.
→ Check whether the model was trained on many targets without proper termination.
```

IF both base and fine-tuned models fail similarly:

```text
→ Suspect generation configuration or chat-template handling before blaming fine-tuning.
```

Transformers generation explicitly relies on configured special-token IDs such as `eos_token_id` and `pad_token_id`, so these should be treated as part of the evaluation configuration rather than incidental defaults.

---

# 14. Checkpoint Selection

The final checkpoint is not automatically the best checkpoint.

Do not select solely by:

```text
minimum training loss
```

or even:

```text
minimum validation loss
```

when the actual use case is generation.

Prefer metrics that represent the intended behavior.

Examples:

```text
task accuracy
exact match
tool-call success
execution success
schema validity
test pass rate
human evaluation
LLM-as-a-Judge
```

Choose the checkpoint that performs best on the target capability while respecting the capability budget.

---

# 15. After Training

A completed training job is not proof that the model improved.

Always run the baseline evaluation suite again.

Compare:

```text
Base Model
vs
Fine-tuned Model
```

Measure:

```text
target capability
supporting capabilities
general regressions
format behavior
instruction following
qualitative behavior
```

---

# 16. Manual Output Inspection

Automatic metrics are not enough for many LLM tasks.

Inspect representative outputs side by side.

Look for:

```text
correctness
naturalness
instruction following
verbosity
repetition
hallucination
formatting
style drift
refusal behavior
stopping behavior
```

A benchmark may improve while user-visible behavior becomes worse.

---

# 17. Failure Diagnosis

## Case A — Model does not learn

IF:

```text
training loss remains flat
tiny overfit fails
```

THEN check:

```text
labels
masking
trainable parameters
learning rate
target modules
gradient flow
dataset formatting
optimizer
```

---

## Case B — Tiny overfit passes, full training does not improve

THEN investigate:

```text
data quality
data diversity
task difficulty
learning rate
training duration
adapter capacity
base-model capability
```

This usually means the basic training pipeline works and the bottleneck lies elsewhere.

---

## Case C — Training improves, validation does not

Likely causes:

```text
overfitting
insufficient diversity
too many training steps
learning rate too high
excess adapter capacity
dataset too small or narrow
```

Possible response:

```text
shorter training
lower learning rate
better data
adjust regularization
adjust adapter capacity
```

---

## Case D — Validation improves, real usage does not

Suspect evaluation mismatch.

Check:

```text
Does validation represent real usage?

Is there leakage?

Is production prompting different?

Is generation config different?

Is the benchmark too narrow or too easy?
```

---

## Case E — Formatting improves, capability does not

Example:

```text
JSON validity ↑
task accuracy ≈
```

The model may have learned output structure without learning the underlying task.

Consider:

```text
better capability-focused data
greater task diversity
different training objective
stronger base model
```

---

## Case F — Target capability improves, general capability drops

This may be acceptable.

Ask:

```text
Was the regression expected?

Is the model intended to be a specialist?

Did supporting capabilities remain intact?

Is the trade-off within the capability budget?
```

For a specialist SLM, sacrificing unrelated capability can be a valid design decision.

---

## Case G — An important supporting capability drops

Treat supporting capabilities differently from unrelated benchmarks.

A tool-calling specialist may tolerate lower broad knowledge.

It should not tolerate major regressions in capabilities such as:

```text
instruction following
argument extraction
JSON validity
basic reasoning required for tool selection
```

Always distinguish:

```text
target capability
supporting capability
non-target capability
```

---

## Case H — Model ignores EOS or loops

Use the diagnosis in Section 13.

Prioritize:

```text
training target termination
chat template
truncation
packing
EOS/end-of-turn labels
generation configuration
```

before changing optimization hyperparameters.

---

# 18. Choosing the Next Change

Change the variable that matches the diagnosed problem.

Do not tune blindly.

## 18.1 Magnitude heuristic

Changes should usually be large enough to produce a measurable experimental difference.

Avoid wasting runs on changes such as:

```text
learning rate:
2e-4 → 1.9e-4
```

unless you are already in a narrow final tuning stage.

For early experiments, useful search steps are often approximately:

```text
Learning rate:
change by roughly 2× when probing sensitivity

2e-4 → 1e-4 → 5e-5
```

```text
LoRA rank:
test meaningful capacity changes

8 → 16 → 32
```

```text
Micro/effective batch:
halve or double when studying batch effects
```

These are heuristics, not laws.

Do not mechanically double or halve parameters when:

```text
a published/model-specific recipe suggests otherwise
the current run is already close to the desired operating point
memory constraints restrict the search
the parameter interacts strongly with another variable
```

The goal is to create experiments with enough separation to learn something from them.

---

## 18.2 Match the change to the symptom

Problem:

```text
Overfitting
```

Possible change:

```text
fewer steps
better data diversity
lower learning rate
lower adapter capacity
more appropriate regularization
```

Problem:

```text
Tiny overfit fails
```

Possible action:

```text
Do not tune dataset scale yet.
Fix the training pipeline first.
```

Problem:

```text
Model learns too little
```

Possible change:

```text
learning rate
training duration
data quality
adapter capacity
```

Problem:

```text
Formatting improves but task accuracy does not
```

Possible change:

```text
more capability-focused examples
better target construction
different training objective
```

Problem:

```text
General regressions are too large
```

Possible change:

```text
less aggressive training
more diverse data
mixed-domain examples
reduced adapter capacity
```

---

# 19. Experiment Loop

Every iteration should answer:

```text
What changed?

Why did we change it?

What did we expect?

What happened?

What should happen next?
```

Example:

```text
exp-001
Initial QLoRA run

exp-002
Same config, improved dataset

exp-003
Same data, lower learning rate

exp-004
Same data and LR, different LoRA capacity
```

Prefer one primary hypothesis per experiment.

---

# 20. Stop Conditions

Fine-tuning should not continue indefinitely.

Stop or reconsider when:

```text
target improvement plateaus
regressions exceed the capability budget
new runs produce negligible gains
data quality is clearly the bottleneck
the base model is too weak
another method is more appropriate
```

Possible decisions:

```text
keep current checkpoint
improve dataset
change hyperparameters
change training method
switch base model
stop fine-tuning
```

Sometimes the correct conclusion is that fine-tuning is not the right solution.

---

# 21. Pre-Run Checklist

Before a full run:

```text
□ Target capability is defined.

□ Success metric is defined.

□ Baseline exists.

□ Capability budget exists.

□ Dataset was manually inspected.

□ Leakage was checked.

□ Chat template is correct.

□ Tokenized samples were inspected.

□ Masking is correct.

□ EOS/end-of-turn behavior is correct.

□ Sequence-length distribution is known.

□ Truncation was inspected.

□ Packing was verified if enabled.

□ LoRA target modules are intentional.

□ Trainable parameter count is correct.

□ Effective batch size is known.

□ Smoke test passed.

□ Tiny overfit test passed.

□ Experiment tracking works.

□ Config is saved.

□ Model and dataset revisions are pinned.
```

If these conditions are satisfied, the experiment is ready for a full training run.

---

# 22. Post-Run Checklist

After training:

```text
□ Training completed without unexplained instability.

□ Selected checkpoints were evaluated.

□ Baseline and fine-tuned evaluation settings match.

□ Target capability was measured.

□ Supporting capabilities were measured.

□ General regressions were measured.

□ EOS / stopping / repetition behavior was checked.

□ Representative outputs were manually inspected.

□ Results were recorded.

□ The experiment hypothesis was answered.

□ The next action is documented.
```

A completed training job is not a completed experiment until these checks are finished.