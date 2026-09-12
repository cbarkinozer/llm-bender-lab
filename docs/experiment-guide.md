# Experiment Guide

This document defines how experiments are created, organized, changed, tracked, and completed inside `llm-bender-lab`.

It does not define training strategy, dataset quality rules, evaluation methodology, or reproducibility details.

See:

* `finetuning-playbook.md`
* `dataset-guide.md`
* `evaluation-guide.md`
* `reproducibility.md`

The goal is to keep experiment history understandable, comparable, and reproducible over time.

---

# 1. Core Principle

An experiment should test a clear hypothesis.

Every experiment should answer:

```text
What changed?
Why did we change it?
What did we expect?
What happened?
What did we learn?
What should happen next?
```

Prefer **one primary hypothesis per experiment**.

Avoid simultaneously changing:

```text
dataset
learning rate
LoRA rank
training duration
prompt format
evaluation settings
```

unless the experiment explicitly studies a combined recipe.

---

# 2. Experiment Hierarchy

Experiments are organized by:

```text
domain
→ model
→ experiment
```

Example:

```text
experiments/
└── turkish-capability/
    └── qwen3.5-0.8b/
        ├── README.md
        ├── exp-000-baseline/
        ├── exp-001-qlora/
        ├── exp-002-data-v2/
        └── exp-003-lr-1e-4/
```

The domain describes the capability being studied.

Examples:

```text
turkish-capability
tool-calling
structured-output
unit-test-generation
code-generation
```

Do not organize experiments primarily by framework.

Bad:

```text
experiments/
├── unsloth/
├── axolotl/
└── transformers/
```

Better:

```text
experiments/
└── tool-calling/
    └── qwen3.5-0.8b/
        └── exp-001-qlora/
```

Framework choice is an implementation detail.

---

# 3. Experiment Naming

Use:

```text
exp-NNN-short-description
```

Examples:

```text
exp-000-baseline
exp-001-qlora
exp-002-data-v2
exp-003-lr-1e-4
exp-004-rank-32
```

Rules:

* use zero-padded sequential IDs,
* use lowercase,
* use only letters, numbers, and hyphens in the description,
* keep the description to roughly 1–3 short terms,
* keep the description part at or below 25 characters,
* describe the main change or purpose,
* do not encode the entire hypothesis into the folder name.

Avoid:

```text
final
final-v2
best
latest
new-final
really-final
exp-004-lowering-learning-rate-to-1e-4-because-of-instability
```

The experiment ID is permanent.

Do not casually rename completed experiments.

---

# 4. Baseline Experiment

Every new model/domain combination should normally begin with:

```text
exp-000-baseline
```

It represents the untouched base model.

It should record:

```text
model revision
evaluation configuration
benchmark revisions
generation configuration
baseline metrics
useful raw outputs
results summary
```

No training happens in `exp-000-baseline`.

The baseline should exist before fine-tuning experiments begin.

---

# 5. When to Create a New Experiment

Create a new experiment when a meaningful experimental variable or hypothesis changes.

Examples:

```text
dataset revision
learning rate
LoRA rank
target modules
training duration
training objective
prompt/training format
preprocessing strategy
```

A base-model change normally starts a new model directory rather than merely another experiment.

Example hypotheses:

```text
exp-001
Can QLoRA improve Turkish capability?

exp-002
Does curated data improve over exp-001?

exp-003
Does a lower learning rate reduce regression?
```

---

# 6. When NOT to Create a New Experiment

Do not create a new experiment for an operational rerun when the hypothesis and configuration remain unchanged.

Examples:

```text
machine crashed
network disconnected
W&B logging failed
checkpoint upload failed
same training run resumed
```

Track those as separate **runs** under the same experiment.

```text
Experiment:
exp-003-lr-1e-4

Runs:
run-01
run-02
```

---

# 7. Meaningful Changes

Early experiments should differ enough to teach us something.

Usually unhelpful:

```text
learning rate:
2e-4 → 1.9e-4
```

More useful during exploration:

```text
2e-4 → 1e-4
```

Similarly:

```text
LoRA rank:
16 → 17
```

usually teaches little compared with:

```text
16 → 32
```

These are heuristics, not laws.

Small changes may become useful during later narrow optimization.

---

# 8. Required Experiment Files

A training experiment should normally contain:

```text
exp-001-qlora/
├── README.md
├── config.yaml
└── results/
```

Experiment-specific scripts may also exist when necessary:

```text
train.py
evaluate.py
```

But reusable implementations should live under shared project code such as:

```text
llm_bender_lab/
├── training/
├── evaluation/
└── data/
```

Do not duplicate large training scripts between experiment directories merely to change configuration values.

---

# 9. Experiment README

Every experiment should contain a concise README.

Recommended structure:

```markdown
# exp-001-qlora

## Status
## Goal
## Hypothesis
## Parent Experiment
## What Changed
## Base Model
## Dataset
## Training Setup
## Evaluation
## Results
## Regressions
## Conclusion
## Next Step
```

The experiment README records the experiment.

It is not the place for general fine-tuning theory.

---

# 10. Experiment Status

Use:

```text
planned
ready
running
failed
completed
selected
abandoned
```

### `planned`

The hypothesis exists but the experiment is not ready.

### `ready`

Data, configuration, evaluation, and required checks are ready.

### `running`

At least one active run is executing.

### `failed`

A technical or methodological problem prevented a valid evaluation of the hypothesis.

### `completed`

The experiment ran, was evaluated, and produced a valid result.

### `selected`

The experiment currently contains the preferred candidate for the intended use case.

### `abandoned`

The experiment was intentionally stopped or superseded before producing a result.

Do not mark an experiment `completed` merely because training finished.

---

# 11. Goal

The goal describes what should improve.

Good:

```text
Improve Turkish language benchmark performance using QLoRA.
```

Better:

```text
Improve Turkish benchmark performance while keeping instruction-following
regression inside the predefined capability budget.
```

Bad:

```text
Try LoRA.
```

The method is not the goal.

---

# 12. Hypothesis

A hypothesis should state the expected effect of the change.

Example:

```text
A curated 5k-example Turkish dataset will improve target Turkish performance
over the 2k dataset used in exp-001 without materially increasing
instruction-following regression.
```

Prefer falsifiable hypotheses.

---

# 13. Parent Experiment and Lineage

Every non-baseline experiment should identify its primary parent/comparison experiment.

```yaml
experiment:
  id: exp-003-lr-1e-4
  parent: exp-002-data-v2
```

Example:

```text
exp-000-baseline
      ↓
exp-001-qlora
      ↓
exp-002-data-v2
      ↓
exp-003-lr-1e-4
```

Branches are allowed:

```text
             exp-001
             /     \
        exp-002   exp-003
```

Always make the lineage explicit.

---

# 14. What Changed

Record the main difference from the parent experiment.

Example:

```text
Changed:
learning rate: 2e-4 → 1e-4

Unchanged:
dataset
LoRA rank
target modules
epochs
evaluation protocol
```

This should make it possible to understand the experiment without manually diffing several files.

---

# 15. Experiment Configuration

Every experiment must have a **complete, self-contained** `config.yaml`.

Do not use delta-only experiment configs or undocumented inheritance for important experiment settings.

When creating a child experiment:

```text
1. Copy the complete config.yaml from the parent experiment.
2. Change experiment.id.
3. Set experiment.parent to the parent experiment.
4. Change only the fields required by the new hypothesis.
5. Review the resulting full config before running.
```

This prevents defaults or inherited settings from becoming invisible.

Example:

```yaml
experiment:
  id: exp-003-lr-1e-4
  parent: exp-002-data-v2
  status: ready

model:
  name: Qwen/Qwen3.5-0.8B
  revision: "<exact-revision>"

dataset:
  name: "<dataset-repo>"
  revision: "<exact-revision>"

training:
  framework: unsloth
  method: qlora
  seed: 42

  max_seq_length: 2048

  learning_rate: 1e-4
  epochs: 2

  micro_batch_size: 2
  gradient_accumulation_steps: 8

  lora_rank: 16
  lora_alpha: 32
  lora_dropout: 0

evaluation:
  config: configs/evaluation/turkish-v1.yaml

tracking:
  provider: wandb
  project: llm-bender-lab
```

The schema may evolve, but important experiment parameters should remain explicit.

---

# 16. Shared Code vs Experiment-Specific Code

Prefer shared implementations when behavior is identical.

Experiment folders should primarily contain:

```text
configuration
hypothesis
results
experiment-specific glue
```

Create experiment-specific code only when the experiment genuinely changes implementation behavior.

---

# 17. Framework Changes

Changing framework does not automatically mean a new scientific experiment.

Example:

```text
Unsloth → native TRL/PEFT
```

may simply be an implementation-validation rerun if the intended effective training configuration is identical.

Create a new experiment when:

```text
the framework comparison is itself the hypothesis
packing or masking changes
optimizer behavior changes materially
the effective training procedure changes
numerical behavior becomes relevant to the experiment
```

Document why.

---

# 18. Run IDs

One experiment may contain multiple runs.

Example:

```text
exp-004-rank-32

run A:
machine failed

run B:
completed
```

Use W&B or another tracker to retain run identities.

Store relevant IDs in experiment metadata.

```yaml
runs:
  - provider: wandb
    id: abc123
    status: failed

  - provider: wandb
    id: def456
    status: completed
```

Do not create another experiment merely because an identical run had to restart.

---

# 19. Failed Experiments

Do not delete failed experiments if they contain useful information.

Useful failures include:

```text
configuration does not fit memory
learning rate causes instability
dataset format is invalid
framework/model combination fails
training strategy is unsuitable
```

Record:

```text
what failed
where it failed
suspected cause
whether the failure was technical or experimental
next action
```

Do not create permanent experiment entries for trivial development mistakes that never constituted a real experiment.

---

# 20. Technical Failure vs Experimental Failure

Distinguish the two.

## Technical failure

The hypothesis was not validly tested.

Examples:

```text
CUDA OOM
broken dependency
corrupt checkpoint
network interruption
invalid dataset schema
```

## Experimental failure / negative result

The experiment ran correctly but the hypothesis was unsupported.

Examples:

```text
target metric did not improve
regressions exceeded capability budget
new dataset performed worse
```

Negative results are valid experiment results.

Do not “fix the code” merely because the scientific result was negative.

---

# 21. Results Directory

Keep small useful artifacts:

```text
results/
├── summary.json
├── metrics.json
├── comparison.csv
└── samples.jsonl
```

Do not store large checkpoints, full model weights, or large generated datasets here.

---

# 22. Checkpoint Management

Checkpoint retention must be intentional.

Training checkpoints can consume large amounts of disk space, especially across repeated experiments.

During an active run:

```text
→ Keep enough recent checkpoints to recover from interruption.
→ Use a reasonable retention limit.
→ Do not save checkpoints more frequently than the experiment requires.
```

A default such as:

```text
save_total_limit: 2
```

can be reasonable for many experiments, but it is **not a universal rule**.

Increase retention when:

```text
checkpoint comparison is part of the experiment
the best checkpoint may occur well before the end
resume/recovery requirements justify it
```

Before deleting anything, make sure the checkpoint required for evaluation or publication has been preserved.

After an experiment is completed and checkpoint selection is finished:

```text
→ Keep the selected checkpoint or adapter.
→ Keep another checkpoint only if it has a documented purpose.
→ Remove redundant intermediate checkpoints.
→ Remove temporary optimizer/training state if no longer needed for resume.
```

Do not automatically keep a separate “final” checkpoint if it has no purpose.

Do not delete checkpoints while an active run may still need them for recovery.

Large released artifacts belong in the appropriate artifact store, not permanently in the Git repository or temporary GPU disk.

---

# 23. Result Summary Schema

Prefer a small machine-readable summary.

```json
{
  "experiment_id": "exp-003-lr-1e-4",
  "status": "completed",
  "selected_checkpoint": "checkpoint-1200",
  "metrics": {
    "turkish_target": 58.2,
    "instruction_following": 51.7,
    "general_reasoning": 26.1
  },
  "baseline": {
    "turkish_target": 44.8,
    "instruction_following": 52.1,
    "general_reasoning": 29.7
  }
}
```

Never invent unmeasured metrics.

---

# 24. Comparing Experiments

Use compact comparison tables where useful.

| Experiment | Turkish | IFEval | General | Main Change   |
| ---------- | ------: | -----: | ------: | ------------- |
| exp-000    |    44.8 |   52.1 |    29.7 | Base model    |
| exp-001    |    54.1 |   51.8 |    28.9 | Initial QLoRA |
| exp-002    |    58.2 |   51.7 |    28.6 | Better data   |
| exp-003    |    59.0 |   52.0 |    29.1 | Lower LR      |

Do not directly compare experiments that used materially different evaluation protocols without clearly marking that difference.

---

# 25. Selecting an Experiment

Mark an experiment:

```text
selected
```

when it currently contains the preferred candidate for the intended use case.

Selection should consider:

```text
target metric
supporting capabilities
capability budget
qualitative behavior
deployment constraints
```

The highest target score is not automatically the best model.

Example:

```text
exp-004
target = 61
instruction regression = -12

exp-005
target = 59
instruction regression = -1
```

`exp-005` may be preferable.

Only one experiment should normally be marked as the current selected candidate for the same model/domain objective unless multiple deployment profiles are intentionally maintained.

---

# 26. Selected Checkpoint

Record the exact selected checkpoint or artifact.

Bad:

```text
best checkpoint
```

Good:

```text
checkpoint-1200
```

Better when published:

```text
HF artifact + exact revision
```

Record why it was selected.

---

# 27. Experiment Completion

An experiment is complete only when:

```text
training produced a valid result
evaluation finished
results were recorded
regressions were analyzed
hypothesis was answered
next action was documented
```

Training completion alone is insufficient.

---

# 28. Closing an Experiment

The final README should answer:

```text
Did the hypothesis hold?

Did the target capability improve?

What regressed?

Were the regressions acceptable?

What evidence supports the conclusion?

What should be tested next?
```

Avoid:

```text
Model seems better.
```

Prefer:

```text
Turkish target accuracy improved by 8.4 points while instruction-following
changed by -0.6 points. The experiment therefore met the predefined target
and regression budget.
```

---

# 29. Cascading Updates

Experiment state must remain consistent across the repository.

When an experiment changes state or completes:

```text
1. Update the experiment's README.
2. Update its result files.
3. Update its config/status metadata where applicable.
4. Update the parent model/domain README:
   experiments/<domain>/<model>/README.md
5. Update the Experiment Registry entry.
6. If the experiment became selected:
   update the previous selected experiment's status/reference as needed.
```

Do not leave:

```text
exp-002/README.md → completed
```

while the parent registry still says:

```text
exp-002 → running
```

The local experiment directory is the detailed record.

The parent registry is the current index.

Both must agree.

---

# 30. Experiment Branching

Experiments may branch.

```text
exp-001-qlora
├── exp-002-more-data
├── exp-003-lower-lr
└── exp-004-rank-32
```

Always record the parent.

Use branches when several independent hypotheses should be tested from the same starting point.

---

# 31. Combining Successful Changes

Do not assume individually useful changes combine additively.

Example:

```text
exp-002:
better data works

exp-003:
lower LR works
```

Then create:

```text
exp-004-data-v2-lower-lr
```

to test their combination.

Combined recipes are new hypotheses.

---

# 32. Experiment Registry

Each model/domain directory should maintain a concise registry:

```markdown
| ID | Status | Main Change | Target Score | Notes |
|---|---|---|---:|---|
| exp-000 | completed | baseline | 44.8 | Base model |
| exp-001 | completed | initial QLoRA | 54.1 | First gain |
| exp-002 | selected | data v2 | 58.2 | Current best |
| exp-003 | planned | lower LR | - | Next |
```

Location:

```text
experiments/<domain>/<model>/README.md
```

Keep detailed experiment information inside each experiment directory.

---

# 33. Model-Level README

The model/domain README should summarize:

```text
target capability
base model
baseline
capability budget
evaluation suite
current selected experiment
experiment registry
```

Do not duplicate every experiment's full report.

---

# 34. Do Not Rewrite Historical Results

Completed experiments are historical records.

If a bug is discovered later:

```text
→ Do not silently replace old results.
```

Instead:

```text
1. Document the issue.
2. Mark affected results invalid or superseded where necessary.
3. Correct the implementation.
4. Re-run or re-evaluate under a new traceable revision.
```

Traceability matters more than making history look clean.

---

# 35. Evaluation Changes

Changing evaluation methodology can invalidate comparisons.

If evaluation changes:

```text
→ version the evaluation configuration
→ record the new version
→ re-evaluate important previous checkpoints when practical
```

Do not compare:

```text
evaluation-v1
```

with:

```text
evaluation-v2
```

as though they were identical.

See `evaluation-guide.md`.

---

# 36. Dataset Changes

Dataset modifications must reference an exact revision.

Avoid:

```yaml
dataset: turkish-sft
```

Prefer:

```yaml
dataset:
  repo: ...
  revision: ...
```

A material dataset change normally creates a new experiment.

See `dataset-guide.md`.

---

# 37. Reproducibility Metadata

Each experiment should ultimately be traceable to:

```text
Git commit
base model revision
dataset revision
full experiment config
environment
seed
evaluation config
run ID
selected checkpoint/artifact
```

See `reproducibility.md`.

---

# 38. Before Creating a New Experiment

Ask:

```text
□ What is the hypothesis?

□ What is the parent experiment?

□ What exactly changes?

□ Is the change meaningful enough to test?

□ What remains constant?

□ How will success be measured?

□ Does this need a new experiment or only another run?

□ Is the existing evaluation protocol still compatible?

□ Was the parent's full config copied and reviewed?
```

If these cannot be answered, the experiment is not ready.

---

# 39. Before Marking an Experiment Completed

Check:

```text
□ A valid training/result run exists.

□ Evaluation completed.

□ Result summary exists.

□ Comparison with parent/baseline exists.

□ Regressions were checked.

□ Hypothesis was answered.

□ Run IDs are recorded.

□ Selected checkpoint is recorded if relevant.

□ Redundant checkpoints were reviewed for cleanup.

□ Experiment README conclusion is complete.

□ Parent Experiment Registry was updated.

□ Next step is documented.
```

---

# 40. Agent Rules

When an agent works with experiments:

```text
IF creating a new experiment:
→ identify the parent
→ copy the parent's complete config.yaml
→ update id and parent
→ modify only variables required by the hypothesis
→ state the hypothesis
→ preserve previous experiments
```

```text
IF restarting an identical run:
→ do not create a new experiment
→ create or record a new run ID
```

```text
IF an experiment completes:
→ update local README
→ update result files
→ update status
→ update experiments/<domain>/<model>/README.md
→ update the Experiment Registry
→ never leave parent and child status inconsistent
```

```text
IF an experiment becomes selected:
→ record the exact selected checkpoint/artifact
→ update the model-level README
→ update any previous "selected" status if appropriate
```

```text
IF checkpoint storage grows:
→ preserve checkpoints needed for active recovery/evaluation
→ prune redundant checkpoints only after confirming they are unnecessary
→ never commit checkpoints to Git
```

```text
IF a completed experiment must be corrected:
→ do not silently overwrite history
→ document the issue
→ create a traceable corrected run, experiment, or evaluation revision
```

```text
IF several experimental variables are changing:
→ verify that the combined change is intentional
→ otherwise split the hypotheses
```

```text
IF the experiment has no measurable goal:
→ stop
→ define the goal before training
```

---

# 41. Minimal Experiment Lifecycle

Normal path:

```text
planned
↓
ready
↓
running
↓
completed
```

Alternative transitions:

```text
running → failed
planned → abandoned
completed → selected
```

A selected experiment may later be superseded.

Do not delete it.

---

# 42. Final Principle

The experiment history should tell a coherent story.

Someone opening the repository months later should understand:

```text
where we started
what we changed
why we changed it
what improved
what regressed
what failed
what became the selected model
```

The goal is not to accumulate runs.

The goal is to accumulate **evidence**.
