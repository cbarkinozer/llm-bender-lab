# Reproducibility

This document defines how experiments in `llm-bender-lab` are made reproducible, traceable, recoverable, and auditable.

The objective is not to pretend that modern LLM training is perfectly deterministic.

The objective is to make it possible to determine:

```text
What code ran?
What command started it?
What model and tokenizer were loaded?
What data was used?
How was that data produced?
What configuration actually took effect?
What hardware and numerical backend executed it?
What artifact was produced?
How was it evaluated?
Can the process be reconstructed later?
```

For training decisions, see `finetuning-playbook.md`.

For experiment organization, see `experiment-guide.md`.

For dataset provenance, see `dataset-guide.md`.

For evaluation reproducibility, see `evaluation-guide.md`.

---

# Part I — Reproducibility Model

## 1. Core Principle

Every meaningful experiment should preserve enough evidence to reconstruct its lineage.

At minimum:

```text
Git commit
entrypoint and CLI arguments
starting model revision
tokenizer revision
dataset revision
dataset-builder revision
full effective training configuration
random seeds
environment
hardware
numerical/backend configuration
evaluation configuration
run ID
selected checkpoint/artifact
```

A metric without provenance is an observation.

A traceable metric becomes evidence.

---

## 2. Reproducibility Has Multiple Levels

### Exact reproducibility

The same experiment produces effectively identical:

```text
weights
outputs
training trajectory
metrics
```

This may require:

```text
same hardware
same topology
same framework versions
same CUDA/cuDNN stack
same kernels
same seeds
same data order
same attention backend
same numerical settings
deterministic algorithms
```

Bitwise identity should not be assumed unless it was explicitly tested.

---

### Statistical reproducibility

Repeated runs are not identical but produce equivalent outcomes within expected run-to-run variation.

Example:

```text
Run A: 58.1
Run B: 57.8
Run C: 58.4
```

For many LLM experiments this is more meaningful than demanding identical weights.

---

### Procedural reproducibility

Another engineer or agent can reconstruct the complete procedure and rerun it.

This requires:

```text
code
configs
model revisions
dataset revisions
environment
hardware assumptions
evaluation protocol
artifact lineage
```

Procedural reproducibility is the minimum standard for reportable experiments in this repository.

---

# Part II — Run Manifest and Artifact Identity

## 3. Every Meaningful Run Gets a Manifest

Create a machine-readable manifest for each experimental run.

Example:

```json
{
  "experiment_id": "exp-003-lr-1e-4",
  "run_id": "abc123",
  "git_commit": "5f7a1c2...",
  "git_dirty": false,

  "entrypoint": "python train.py",
  "argv": [
    "train.py",
    "--config",
    "config.yaml"
  ],

  "model": {
    "repo": "Qwen/...",
    "revision": "..."
  },

  "tokenizer": {
    "repo": "Qwen/...",
    "revision": "..."
  },

  "dataset": {
    "repo": "cbarkinozer/...",
    "revision": "..."
  },

  "dataset_builder_git_commit": "...",

  "seed": 42,

  "training": {
    "framework": "unsloth",
    "method": "qlora"
  },

  "hardware": {
    "gpu": "NVIDIA RTX 4090",
    "gpu_count": 1
  },

  "evaluation_config": "turkish-v1"
}
```

The schema may evolve.

The requirement is traceability, not a particular JSON layout.

---

## 4. Record the Effective Configuration

`config.yaml` is not necessarily the configuration that actually ran.

Possible overrides include:

```text
CLI arguments
environment variables
framework defaults
runtime-computed values
launcher configuration
```

Therefore preserve both:

```text
source config
+
resolved/effective config
```

If the framework exposes its final trainer configuration, serialize it after all overrides have been applied.

---

## 5. Record the Exact Entrypoint

Store:

```text
script/module
working directory
CLI arguments
launcher
```

Examples:

```text
python train.py --config config.yaml
```

or:

```text
torchrun --nproc-per-node=4 train.py --config config.yaml
```

In Python, capturing `sys.argv` is a simple baseline.

This prevents hidden CLI overrides from disappearing from experiment history.

---

## 6. Record Run Identity, Not Only Experiment Identity

`exp-003` alone does not uniquely identify a result.

A complete identity may include:

```text
experiment ID
run ID
checkpoint
artifact revision
evaluation revision
```

---

## 7. Record Model and Tokenizer Revisions

Do not preserve only repository names.

Prefer:

```yaml
model:
  repo: Qwen/...
  revision: "<immutable-revision>"

tokenizer:
  repo: Qwen/...
  revision: "<immutable-revision>"
```

Repositories and templates can evolve.

---

## 8. Record the Chat Template

Preserve:

```text
tokenizer revision
chat template source
template content or hash
special token configuration
```

For important runs, preserving the actual template text is safer than assuming it can always be reconstructed later.

---

## 9. Record Dataset Artifact Revision

Use an immutable dataset revision when available.

Example:

```yaml
dataset:
  repo: cbarkinozer/turkish-sft
  revision: "<hf-commit>"
```

Avoid relying only on:

```text
main
latest
```

---

## 10. Record Dataset Construction Provenance

The dataset artifact is only one side of reproducibility.

Also preserve:

```text
builder Git commit
source revisions
generation scripts
filtering configuration
deduplication logic
split logic
sampling logic
```

---

## 11. Record Data-Processing Seeds

Dataset construction may contain randomized operations.

Examples:

```text
sampling
shuffling
train/validation splitting
MinHash permutation generation
clustering initialization
synthetic generation
```

Record every relevant seed.

Do not assume the training seed also controls dataset construction.

---

## 12. Synthetic Data Manifest

Record:

```text
provider
model/version
generation prompt
temperature
top_p
max tokens
seed if supported
generation date
post-processing
filtering
```

If the provider is nondeterministic or mutable:

```text
→ preserve the generated dataset artifact
→ document that exact regeneration may be impossible
```

---

## 13. Artifact Hashes

For important exported artifacts, record a cryptographic hash where practical.

Example:

```text
SHA-256
```

Useful targets include:

```text
adapter
merged weights
GGUF
evaluation output bundle
manifest
```

This verifies artifact identity independently of filenames.

---

## 14. Preserve Artifact Lineage

Every final artifact should be traceable through transformations.

Example:

```text
Base Model @ revision A
+
LoRA Adapter @ artifact B
↓
merge_model.py @ Git commit C
↓
BF16 merged model
↓
quantize.py @ Git commit D
↓
Q4_K_M GGUF @ hash E
```

---

# Part III — Code, Environment and Numerical Backend

## 15. Record the Git Commit

Every reportable run should record:

```text
git_commit
```

Do not use a branch name as the only code identifier.

---

## 16. Dirty Working Trees

Before a full experiment:

```text
IF working tree is clean:
→ continue

IF working tree is dirty:
→ preferably commit intended changes
→ otherwise preserve the exact diff
→ mark the run as dirty
```

Do not silently claim a clean Git revision when uncommitted code affected the run.

---

## 17. Preserve the Python Environment

Record relevant versions such as:

```text
Python
PyTorch
Transformers
TRL
PEFT
Accelerate
Datasets
bitsandbytes
Unsloth
flash-attn if independently installed
W&B
```

Prefer a lockfile when practical.

Examples:

```text
uv.lock
requirements lock
Poetry lock
Conda export
```

---

## 18. Record Runtime Environment Variables

Some environment variables materially affect execution.

Capture a **sanitized allowlist** or filtered environment snapshot.

Potentially relevant variables include:

```text
CUDA_VISIBLE_DEVICES
OMP_NUM_THREADS
MKL_NUM_THREADS
TOKENIZERS_PARALLELISM

NCCL_*
CUDA_*
CUBLAS_*
TORCH_*
HF_*
TRANSFORMERS_*
```

Examples of particularly relevant CUDA/PyTorch variables include:

```text
CUDA_VISIBLE_DEVICES
CUBLAS_WORKSPACE_CONFIG
TORCH_ALLOW_TF32_CUBLAS_OVERRIDE
NVIDIA_TF32_OVERRIDE
```

PyTorch exposes several environment controls that can alter CUDA execution.

Never dump the entire environment blindly.

Strip secrets such as:

```text
HF_TOKEN
WANDB_API_KEY
API keys
cloud credentials
SSH credentials
```

---

## 19. Record Hardware

Capture at least:

```text
GPU model
GPU count
VRAM
CPU architecture where relevant
RAM where relevant
```

For distributed training also record:

```text
node count
GPUs per node
world size
interconnect where relevant
distributed backend
```

---

## 20. Record CUDA and Driver Stack

Record:

```text
NVIDIA driver
PyTorch CUDA runtime
CUDA toolkit if separately relevant
cuDNN version where available
```

Useful runtime metadata may come from:

```text
nvidia-smi
torch.version.cuda
torch.backends.cudnn.version()
```

---

## 21. Record Precision

Capture:

```text
parameter dtype
compute dtype
autocast dtype
quantization dtype
merge dtype
inference dtype
```

Examples:

```text
FP32
BF16
FP16
INT8
NF4
```

Do not record only:

```text
4-bit
```

when the actual quantization configuration contains more information.

---

## 22. Record TF32 / Float32 Matmul Policy

On modern NVIDIA hardware, float32 matrix multiplication policy can materially change numerics and performance.

Record the effective policy, such as:

```python
torch.get_float32_matmul_precision()
```

and relevant backend state when available.

Possible values include:

```text
highest
high
medium
```

Do not assume TF32 is enabled merely because the GPU is Ampere or newer.

Current PyTorch documentation states that the default float32 matmul precision is `highest`, while lower-precision modes can enable faster TF32/BF16-based computation.

Also record relevant convolution precision settings when they matter.

---

## 23. Record Attention Backend

Modern Transformer execution may use:

```text
Flash Attention
memory-efficient SDPA
cuDNN SDPA
math SDPA
third-party flash-attn
architecture-specific kernels
```

PyTorch SDPA may choose among available implementations automatically, and different backends can produce numerically different results.

Record where practical:

```text
attention implementation
SDPA backend policy
flash-attn package version
framework attention setting
```

Examples may include:

```text
attn_implementation
sdpa
flash_attention_2
eager
```

depending on the framework/model.

---

## 24. Record Determinism Settings

Capture relevant settings such as:

```text
torch.use_deterministic_algorithms(...)
torch.backends.cudnn.deterministic
torch.backends.cudnn.benchmark
CUBLAS_WORKSPACE_CONFIG
```

Do not assume:

```text
seed = 42
```

implies deterministic execution.

Some CUDA paths may choose nondeterministic algorithms, while deterministic alternatives can carry a performance cost.

---

## 25. Record Compilation and Kernel Optimization

When relevant record:

```text
torch.compile enabled?
compiler backend
compiler mode
CUDA graphs
custom Triton kernels
Unsloth optimization path
```

Compiler/kernel changes may alter numerical execution and performance.

---

# Part IV — Data Execution Reproducibility

## 26. Raw Data and Training Representation Are Different

Reproducibility requires distinguishing:

```text
raw dataset
↓
formatting
↓
chat template
↓
tokenization
↓
packing
↓
training batches
```

Record enough metadata to reconstruct the actual representation seen by the model.

---

## 27. Runtime Preprocessing Is Allowed, but Must Be Deterministic

Do **not** impose a universal rule that all tokenization must happen ahead of time.

Runtime tokenization can be reproducible if:

```text
input artifact is immutable
tokenizer revision is pinned
template is pinned
processing function is versioned
ordering is deterministic
random transforms are seeded
```

Hugging Face Datasets supports multiprocessing transformations, so multiprocessing itself does not automatically imply irreproducibility.

The actual pipeline must be validated rather than banned categorically.

---

## 28. Ahead-of-Time Tokenization

For expensive, critical, or release-grade runs, pre-tokenizing can reduce moving parts.

Possible flow:

```text
raw dataset revision
↓
tokenization pipeline @ Git commit
↓
tokenized dataset revision
↓
training
```

Benefits:

```text
stable token representation
easier auditing
faster startup
reduced runtime variability
```

But it also couples the artifact to:

```text
tokenizer
chat template
sequence-length policy
packing strategy
```

Therefore AOT tokenization is an option, not a universal default.

---

## 29. Packing Reproducibility

If packing is performed dynamically, record:

```text
packing algorithm
packing seed if applicable
worker count where relevant
shuffle configuration
boundary policy
```

For highly reproducible runs, either:

```text
A. precompute packed sequences
```

or:

```text
B. prove that dynamic packing produces deterministic packed item IDs/order
```

Do not assume multi-worker dynamic packing is reproducible merely because the global seed is fixed.

---

## 30. DataLoader State

Record where relevant:

```text
shuffle
sampler
num_workers
persistent_workers
worker seeding
drop_last
prefetch behavior
distributed sampler
```

For exact resume, data position can matter as much as model state.

---

# Part V — Distributed Training and State Management

## 31. Distributed Configuration Is Part of the Experiment

Record:

```text
DDP / FSDP / DeepSpeed / other
world size
rank layout
nodes
GPUs per node
sharding strategy
offload
mixed precision
gradient accumulation
```

Distributed execution changes the numerical path and batch decomposition.

---

## 32. Resume Is Not Restart

### Resume

Continues from an interrupted training state.

### Restart

Starts again from the initial model/configuration.

Record which one happened.

---

## 33. Full-State Resume

A true resume may require:

```text
model/adapter state
optimizer state
scheduler state
trainer state
RNG state
sampler state/data position
```

If only weights are restored:

```text
→ call it weight initialization from checkpoint
→ do not claim mathematical continuity
```

---

## 34. Distributed RNG State

Distributed training may maintain state per process/rank.

For exact-continuity resume, preserve framework-supported per-rank state where applicable.

A single global seed is not enough to describe distributed runtime state.

---

## 35. Topology-Dependent Resume

For exact or near-exact continuation of distributed training, preserve:

```text
world size
node count
GPUs per node
rank mapping
distributed strategy
```

IF an 8-GPU run resumes on 4 GPUs:

```text
→ do not claim exact continuation
```

The batch distribution, sampler state, communication order, and optimizer behavior may change.

It may still be a valid practical recovery, but classify it accordingly.

---

## 36. Checkpoint Resume Metadata

Record:

```text
checkpoint ID
resume step
original topology
new topology
optimizer restored?
scheduler restored?
RNG restored?
sampler restored?
```

---

## 37. Config Immutability

Once a reportable run starts:

```text
→ never edit its recorded config in place
```

If configuration changes:

```text
→ new run
or
→ new experiment
```

according to `experiment-guide.md`.

---

# Part VI — Evaluation and Downstream Provenance

## 38. Evaluation Is Part of Reproducibility

Record:

```text
evaluation-config revision
benchmark revision
item IDs
prompt version
chat template
generation config
parser/scorer revision
judge configuration
inference backend
precision
batch/padding policy
```

---

## 39. Preserve Per-Item Outputs

Where practical keep:

```text
item ID
prompt
raw output
parsed answer
score
error category
reference
```

This enables:

```text
re-scoring
parser fixes
paired analysis
error analysis
```

without repeating inference.

---

## 40. Version Evaluation Parsers

If parsing/scoring logic changes:

```text
→ create a new evaluation revision
→ re-score saved outputs when possible
```

Do not silently replace historical scoring rules.

---

## 41. Preserve Judge Configuration

For LLM-as-a-Judge store:

```text
provider
judge model/version
prompt
rubric
sampling settings
ordering policy
raw judgment
```

If the provider may change the backend behind a stable model name, preserve outputs and evaluation date.

---

## 42. Model Conversion Is a New Artifact

If an adapter is merged:

```text
adapter
↓
merged model
```

or a model is quantized:

```text
merged model
↓
GGUF
```

record:

```text
source artifact
conversion code commit
conversion command
dtype
parameters
output artifact revision/hash
```

---

## 43. Deployment Configuration Matters

Production reproducibility requires more than weights.

Record:

```text
runtime
runtime version
quantization
KV-cache configuration
generation defaults
serving config
```

---

# Part VII — Network, Caches and External Dependencies

## 44. External Dependencies Can Move

Examples:

```text
Hugging Face Hub
LLM APIs
remote datasets
package indexes
cloud images
```

Pin revisions whenever possible.

---

## 45. Cache State Must Not Define Artifact Identity

Do not say:

```text
the model was whatever happened to be in ~/.cache
```

Resolve the cached content back to its immutable revision.

The manifest should identify the artifact, not merely its local cache path.

---

## 46. Offline Verification

For final verification or highly controlled release runs, offline execution can provide additional assurance.

After all required model/dataset files are cached, optionally run with:

```bash
HF_HUB_OFFLINE=1
```

Hugging Face documents that this disables Hub HTTP calls and requires resources to be available locally.

This can verify:

```text
the pinned artifacts are sufficient
the run does not depend on silent remote fetching
```

It is **recommended for high-assurance verification**, not mandatory for every training run.

Do not enable offline mode before verifying all required artifacts are locally available.

---

## 47. External APIs

For API dependencies record:

```text
provider
model identifier
date
request parameters
prompt
returned output
```

Exact reproduction may become impossible if the provider changes the underlying model.

Preserve outputs when possible.

---

# Part VIII — Run Snapshots and Cloud Recovery

## 48. Automatic Run Snapshot

Before full training begins, automatically preserve:

```text
manifest.json
effective-config.yaml
source-config.yaml
environment metadata
hardware metadata
CLI invocation
sanitized relevant environment variables
Git diff if dirty
```

At run completion append:

```text
run status
selected checkpoint
metrics
artifact revisions
```

---

## 49. Manifest Creation Should Be Automatic

Do not rely on the engineer or agent remembering every field.

Programmatically capture what can be captured.

Manual provenance should be the exception.

---

## 50. Cloud Storage Is Ephemeral

Do not assume:

```text
RunPod disk
Vast.ai disk
temporary VM
local scratch volume
```

is permanent.

Important artifacts must leave ephemeral storage before instance termination.

---

## 51. Before Deleting a Cloud Instance

* [ ] W&B run is synced or backed up.
* [ ] Manifest is saved.
* [ ] Effective configuration is saved.
* [ ] Selected adapter/checkpoint is uploaded.
* [ ] Evaluation outputs are saved.
* [ ] Dataset modifications are versioned.
* [ ] Important logs are preserved.
* [ ] Artifact hashes/revisions are recorded.
* [ ] Nothing important exists only on ephemeral storage.

---

## 52. W&B Offline Failure

If tracking cannot sync:

```text
→ preserve local W&B files
→ preserve run manifest
→ do not delete the instance copy until backup exists
```

Tracking failure should not destroy experiment provenance.

---

# Part IX — Reproducibility Tiers

## 53. Development Run

May be disposable.

Minimum useful metadata:

```text
model
dataset
config
basic logs
```

Do not use development runs as final evidence.

---

## 54. Experimental Run

Require:

```text
Git commit
model revision
dataset revision
full config
seed
run ID
evaluation config
```

---

## 55. Reportable Run

Require:

```text
all experimental metadata
effective configuration
CLI invocation
environment versions
hardware
numerical backend configuration
raw/per-item evaluation where relevant
selected checkpoint
artifact identity
```

---

## 56. Release Run

Require:

```text
all reportable requirements
published artifact revision
artifact lineage
model/dataset documentation
conversion metadata
deployment evaluation
```

For high-assurance release verification, consider:

```text
offline artifact-loading validation
```

---

## 57. Exactness Requirements Scale With Claims

Do not spend large engineering effort achieving bitwise determinism for a throwaway LR probe.

Increase rigor as the run moves from:

```text
development
→ experimental
→ reportable
→ release
```

---

# Part X — Statistical Reproduction and Acceptance

## 58. Multiple Seeds

For important conclusions, repeated runs may be necessary.

Use multiple seeds when you need to distinguish:

```text
real effect
```

from:

```text
seed variation
```

Report where appropriate:

```text
number of runs
mean
variance / standard deviation
confidence interval
```

---

## 59. Define Reproduction Acceptance

Before attempting reproduction, define what success means.

Possible criteria:

```text
same qualitative conclusion
same baseline ranking
same capability-budget decision
task metrics within predefined tolerance
```

Do not invent tolerance after seeing the reproduced result.

---

## 60. Expected Variation

Example:

```text
Target score:
58.1 ± 0.6 across seeds
```

A reproduced score of:

```text
58.3
```

can constitute strong statistical reproduction even if model weights differ.

---

## 61. Reproduction Failure Diagnosis

### Same config, different training trajectory

Check:

```text
seed
dataset order
DataLoader configuration
hardware
topology
PyTorch/CUDA
attention backend
TF32/matmul policy
deterministic settings
```

### Similar training, different evaluation

Check:

```text
checkpoint identity
parser
benchmark revision
generation config
serving backend
quantization
```

### Dataset cannot be regenerated

Check:

```text
source revisions
builder code
dedup seeds
split seeds
synthetic provider
generation prompt
stored artifact
```

---

## 62. Reproducibility Debt

Examples:

```text
unpinned model
unpinned dataset
unknown prompt
unknown CLI override
missing builder commit
dirty tree with no diff
unknown evaluation parser
```

These constitute **reproducibility debt**.

Resolve them before promoting the experiment to:

```text
selected
reportable
release
```

---

# Part XI — Git, Containers and Secrets

## 63. What Belongs in Git

Store:

```text
source code
configs
prompts
evaluation definitions
dataset-building scripts
manifests
small result summaries
documentation
```

---

## 64. What Does Not Belong in Git

Do not commit:

```text
model weights
large checkpoints
large datasets
cache directories
temporary tokenized artifacts
W&B caches
credentials
```

---

## 65. Secrets

Never record secrets inside manifests or environment dumps.

Strip:

```text
HF_TOKEN
WANDB_API_KEY
API keys
cloud credentials
SSH keys
passwords
```

Use:

```text
.env.example
```

for variable names only.

---

## 66. Containers

If containers are used, record:

```text
Dockerfile revision
image repository
tag
image digest
base image
CUDA image version
```

Prefer immutable image digests for important final runs.

---

## 67. Lockfiles and Containers Solve Different Problems

A container helps freeze the operating-system/runtime layer.

A lockfile helps freeze language dependencies.

Neither alone captures:

```text
model
dataset
GPU
driver
runtime flags
external APIs
```

---

# Part XII — Checklists

## 68. Before Starting a Full Experiment

* [ ] Git commit is recorded.
* [ ] Dirty/clean state is recorded.
* [ ] Entrypoint is recorded.
* [ ] CLI arguments are recorded.
* [ ] Model revision is pinned.
* [ ] Tokenizer revision is pinned.
* [ ] Dataset revision is pinned.
* [ ] Dataset-builder commit is known.
* [ ] Dataset-processing seeds are known.
* [ ] Full source config exists.
* [ ] Effective config will be captured.
* [ ] Training seeds are recorded.
* [ ] Environment versions are recorded.
* [ ] Hardware is recorded.
* [ ] CUDA/driver stack is recorded.
* [ ] Precision configuration is recorded.
* [ ] Float32/TF32 matmul policy is recorded.
* [ ] Attention backend is recorded.
* [ ] Relevant deterministic settings are recorded.
* [ ] Relevant environment variables are captured without secrets.
* [ ] Evaluation config is pinned.
* [ ] Run manifest will be generated.

---

## 69. Before Resuming

* [ ] Resume checkpoint is identified.
* [ ] Model state exists.
* [ ] Optimizer state exists if full resume is intended.
* [ ] Scheduler state exists if required.
* [ ] RNG state exists where supported.
* [ ] Sampler/data position is recoverable where required.
* [ ] Original distributed topology is known.
* [ ] Current topology matches if exact continuation is required.
* [ ] Resume vs restart is documented.

---

## 70. Before Marking an Experiment Completed

* [ ] Run ID is recorded.
* [ ] Manifest is complete.
* [ ] Effective config is saved.
* [ ] Selected checkpoint is recorded.
* [ ] Evaluation results are saved.
* [ ] Per-item outputs are preserved where relevant.
* [ ] Environment metadata is preserved.
* [ ] Artifact lineage is recorded.
* [ ] Experiment README is updated.
* [ ] Parent experiment registry is updated.
* [ ] Important artifacts exist outside ephemeral storage.

---

## 71. Before Publishing an Artifact

* [ ] Source experiment is known.
* [ ] Starting model revision is known.
* [ ] Dataset revision is known.
* [ ] Dataset-builder revision is known.
* [ ] Training configuration is available.
* [ ] Environment/framework versions are available.
* [ ] Selected checkpoint is known.
* [ ] Conversion command/configuration is known.
* [ ] Final artifact revision/hash is recorded.
* [ ] Evaluation revision is recorded.
* [ ] Deployment artifact was evaluated.
* [ ] Model card contains lineage.
* [ ] Known reproducibility limitations are documented.
* [ ] Offline loading was optionally validated for high-assurance releases.

---

## 72. Before Destroying Ephemeral Storage

* [ ] Selected artifact is uploaded.
* [ ] Required resume checkpoints are preserved.
* [ ] W&B data is synced or backed up.
* [ ] Manifest is saved.
* [ ] Results are saved.
* [ ] Important logs are saved.
* [ ] Dataset changes are versioned.
* [ ] Evaluation outputs are preserved.
* [ ] Nothing valuable exists only on that machine.

---

# Part XIII — Agent Rules

## 73. Run Creation

```text
IF starting a full experiment:
→ resolve immutable model revision
→ resolve immutable dataset revision
→ record Git commit
→ capture CLI invocation
→ resolve effective config
→ capture runtime environment
→ create manifest before training
```

---

## 74. CLI Overrides

```text
IF CLI arguments override config values:
→ record both source config and resolved effective config
→ treat effective config as what actually ran
```

---

## 75. Runtime Environment

```text
IF an environment variable may affect compute, data loading, distributed execution, or artifact loading:
→ record it in a sanitized runtime snapshot
→ never capture secrets
```

---

## 76. Data Processing

```text
IF preprocessing uses randomness:
→ record its independent seed
```

```text
IF dynamic packing/tokenization is used:
→ verify deterministic ordering for reportable runs
→ otherwise precompute the representation or classify exact reproducibility as unsupported
```

---

## 77. Attention and Precision

```text
IF GPU training is used:
→ record compute dtype
→ record float32 matmul policy
→ record attention implementation/backend
→ record relevant deterministic settings
```

---

## 78. Distributed Resume

```text
IF resuming distributed training with a different world size or topology:
→ do not claim exact continuation
→ document the topology change
```

---

## 79. Network Dependencies

```text
IF external artifacts are loaded:
→ pin immutable revisions
```

```text
IF performing a high-assurance release verification:
→ consider offline loading after all artifacts are cached
```

---

## 80. Missing Provenance

```text
IF critical provenance is missing:
→ do not present the run as fully reproducible
→ explicitly document the gap
```

---

# Final Principle

A reproducible experiment should let another engineer or agent answer:

```text
Which exact code ran?

What command invoked it?

Which effective configuration was used?

Which exact model and tokenizer were loaded?

Which exact dataset was consumed?

How was that dataset produced?

Which random processes occurred?

Which GPU/backend/numerical settings were active?

Which checkpoint became the artifact?

How was it transformed?

How was it evaluated?

Which parts can be reproduced exactly?

Which parts can only be reproduced statistically?
```

Reproducibility does not mean hiding nondeterminism.

It means making the entire experimental state — including its unavoidable uncertainty — **visible and traceable**.
