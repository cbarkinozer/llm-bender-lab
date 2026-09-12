# Dataset Guide

This document defines how datasets are designed, created, validated, split, versioned, and published inside `llm-bender-lab`.

Its purpose is to ensure that training data is:

* relevant to the target capability,
* high quality,
* traceable,
* legally usable,
* reproducible,
* separated from evaluation data,
* correctly formatted for the target model,
* and measurable across versions.

For training decisions, see `finetuning-playbook.md`.

For experiment organization, see `experiment-guide.md`.

For benchmark and metric design, see `evaluation-guide.md`.

For full run traceability, see `reproducibility.md`.

---

# 1. Core Principle

A fine-tuning dataset should teach the capability we want to improve.

Do not optimize for dataset size alone.

Prefer:

```text
small + high quality + diverse + relevant
```

over:

```text
large + noisy + repetitive + poorly targeted
```

Every dataset should answer:

```text
What are we teaching?

Why should this data teach it?

Where did the data come from?

Can we legally use it?

How was quality checked?

How was evaluation leakage prevented?

Can this exact dataset be reconstructed later?
```

---

# 2. Start From the Capability

Do not begin with:

```text
I found a Turkish dataset.
Let's train on it.
```

Begin with:

```text
What capability are we trying to improve?
```

Then map:

```text
Target Capability
↓
Sub-capabilities
↓
Required Behaviors
↓
Example Types
↓
Dataset Composition
```

Example:

```text
Target:
Turkish language capability

Sub-capabilities:
- reading comprehension
- instruction following
- semantic understanding
- grammar
- reasoning in Turkish
- natural answer generation
```

The dataset should follow the experiment goal rather than whatever data happens to be available.

---

# 3. Build a Capability Taxonomy

Define useful categories before generating substantial amounts of data.

Example:

```text
turkish-capability/
├── reading-comprehension
├── reasoning
├── instruction-following
├── grammar
├── summarization
└── structured-response
```

The taxonomy does not need to be perfect.

Its purpose is to make the training distribution visible.

Without it, we may accidentally create:

```text
80% simple QA
10% summarization
10% everything else
```

and later wonder why only simple QA improved.

---

# 4. Dataset Composition

Track important category distributions.

Example:

| Capability            | Samples | Share |
| --------------------- | ------: | ----: |
| Reading comprehension |   1,200 |   24% |
| Reasoning             |   1,000 |   20% |
| Instruction following |   1,000 |   20% |
| Grammar               |     600 |   12% |
| Summarization         |     600 |   12% |
| Structured output     |     600 |   12% |

Equal distribution is not automatically desirable.

The distribution should reflect:

```text
target capability
deployment distribution
known weaknesses
experiment hypothesis
```

---

# 5. Store Semantic Data, Not Model Formatting

Prefer storing conversations in a model-independent representation:

```json
{
  "id": "sample-000001",
  "category": "reasoning",
  "messages": [
    {
      "role": "user",
      "content": "..."
    },
    {
      "role": "assistant",
      "content": "..."
    }
  ]
}
```

Useful optional metadata:

```json
{
  "source": "...",
  "source_id": "...",
  "generation_method": "human|synthetic|transformed",
  "language": "tr",
  "license": "...",
  "quality_status": "accepted"
}
```

Do not permanently bake model-specific tokens such as:

```text
<|im_start|>
<|assistant|>
[INST]
```

into a reusable Hugging Face dataset unless the dataset intentionally targets one fixed format.

Prefer:

```text
raw messages
↓
model tokenizer
↓
model chat template
↓
training representation
```

Apply the exact model/template during preprocessing or training.

---

# 6. SFT, Preference and Other Data Are Different

Do not force every post-training task into the same schema.

## SFT

Typical structure:

```text
conversation
→ desired assistant behavior
```

Example:

```json
{
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

## Preference data

Prefer an explicit shared prompt:

```json
{
  "prompt": [
    {"role": "user", "content": "..."}
  ],
  "chosen": [
    {"role": "assistant", "content": "..."}
  ],
  "rejected": [
    {"role": "assistant", "content": "..."}
  ]
}
```

Keeping the prompt explicit reduces ambiguity over which context belongs to both branches.

Before preference training, verify that:

```text
chosen and rejected use the same intended prompt
chat templating is identical
prompt masking is identical
sequence construction is valid
```

Do not assume an SFT schema is automatically suitable for DPO or another preference objective.

---

# 7. Multi-Turn Conversations

A conversation may contain:

```text
System
User 1
Assistant 1
User 2
Assistant 2
...
```

The loss policy must be explicit.

Possible strategies include:

```text
train on every assistant turn
```

or:

```text
train only on selected assistant turns
```

For normal conversational SFT, a reasonable default is often:

> Train on all assistant turns that represent behavior we want the model to reproduce.

Do not silently train only on the final turn unless that is intentional.

Verify after tokenization which assistant spans contribute to loss.

For each multi-turn sample, check:

```text
Are all intended assistant turns trainable?

Are user/system/tool messages masked?

Are intentionally excluded assistant turns masked?

Did truncation remove the final answer?

Did truncation leave context without its corresponding target?
```

---

# 8. Tool-Calling Data

Tool-use datasets require richer structure than plain user/assistant text.

A conceptual example:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "What is 17 times 24?"
    },
    {
      "role": "assistant",
      "tool_calls": [
        {
          "type": "function",
          "function": {
            "name": "multiply",
            "arguments": {
              "a": 17,
              "b": 24
            }
          }
        }
      ]
    },
    {
      "role": "tool",
      "name": "multiply",
      "content": "408"
    },
    {
      "role": "assistant",
      "content": "The result is 408."
    }
  ]
}
```

Tool definitions should also be preserved where required.

Do not flatten tool data into arbitrary strings before understanding the model's expected chat template.

---

# 9. Tool-Use Loss Policy

Decide explicitly what the model should learn to generate.

Usually the model may need to learn:

```text
assistant tool selection
tool name
tool arguments
final assistant response
```

The environment-generated tool result is normally **context**, not something the model should learn to predict.

Conceptually:

```text
User              → context
Assistant tool call → TRAIN
Tool response       → context
Assistant answer    → TRAIN
```

Actual masking depends on the training framework and model template.

Always inspect resulting labels.

Do not train the model to imitate environment output accidentally.

---

# 10. Reasoning / Rationale Data

Do not treat all long responses as unwanted verbosity.

Distinguish:

```text
useless filler
```

from:

```text
task-relevant rationale or structured reasoning
```

If the target model uses an explicit reasoning format, preserve the model's native format rather than inventing a universal tag such as `<thought>`.

Before using rationale data, decide:

```text
Should the rationale be visible to users?

Should the model learn to generate it?

Does the target model have a native reasoning channel/format?

Should loss include that region?

Is the source of the reasoning trace permitted for training?
```

Do not automatically train on hidden reasoning traces from another system.

---

# 11. Source Provenance

Every dataset should make its origin traceable.

Possible sources:

```text
human-written
public dataset
synthetic generation
transformed source material
internal/domain-specific material
```

Track where relevant:

```text
source
source version
source item ID
license
usage restrictions
transformation method
generation method
```

If origin cannot be reasonably established, investigate before using or publishing the data.

---

# 12. Licensing, Terms and Data-Use Restrictions

Publicly accessible does not mean reusable for model training.

Before using third-party data:

```text
→ identify its license or terms
→ verify model-training use is allowed
→ preserve attribution if required
→ record restrictions
```

Synthetic data has an additional requirement.

Before generating training data through an external API/model:

```text
→ review the provider's current Terms of Service / contract
→ check whether outputs may be used to train or fine-tune another model
→ check publication/commercial-use restrictions
→ record the provider and applicable terms/version
```

Do not assume ownership of generated output automatically means unrestricted model-training rights.

If permission is unclear:

```text
→ stop
→ verify before generating the dataset
```

Do not attempt to bypass provider restrictions by transforming or paraphrasing restricted output.

This guide is not legal advice; uncertain cases require an appropriate legal/compliance review.

---

# 13. Synthetic Data Metadata

For synthetic generation, record:

```text
generator provider
generator model
exact model/version when available
generation prompt/template
temperature
top_p
max tokens
other relevant parameters
seed if supported
generation date
post-processing
filtering
```

If deterministic seeding is unavailable or the API remains nondeterministic, record that limitation.

A stored seed does not guarantee identical API output across:

```text
provider updates
backend changes
model revisions
sampling implementation changes
```

Reproducibility therefore requires preserving the resulting dataset artifact, not merely its generation recipe.

---

# 14. Synthetic Data Diversity

Synthetic datasets commonly develop hidden repetition.

Watch for:

```text
same sentence structure
same answer style
same reasoning pattern
same vocabulary
same prompt framing
same difficulty
```

Vary when appropriate:

```text
topic
difficulty
instruction wording
response length
reasoning pattern
register
task format
```

Thousands of superficially different samples may still have very low effective diversity.

---

# 15. Teacher Model Bias

Synthetic data transfers teacher characteristics.

Potentially inherited:

```text
verbosity
phrasing
formatting habits
refusal behavior
reasoning style
biases
systematic mistakes
```

Always ask:

```text
Do we actually want the student to imitate this?
```

Teacher quality and target behavior are not the same thing.

---

# 16. Multi-Teacher Data

Multiple teachers may increase diversity but can introduce inconsistencies.

If multiple teachers are used:

```text
→ record teacher per sample
→ normalize only what should be normalized
→ apply a common quality filter
→ inspect stylistic conflicts
```

Do not merge sources blindly.

---

# 17. Benchmark Leakage

Benchmark/test data must not enter training.

This includes:

```text
exact questions
answers
paraphrases
translated versions
near-duplicates
synthetic examples derived from benchmark items
solutions/explanations tied to benchmark items
```

The objective is:

```text
teach the capability
```

not:

```text
teach the benchmark
```

---

# 18. Cross-Lingual Contamination

For multilingual experiments, contamination checks must cross language boundaries.

Example:

```text
English GSM-style evaluation item
↓ translated
Turkish training item
```

may still be leakage even when lexical overlap is near zero.

Check for:

```text
translated benchmark datasets
shared source IDs
same underlying problems
same numbers/entities/story structure
known multilingual benchmark variants
machine-translated benchmark releases
```

When possible, compare provenance and canonical source identifiers rather than relying only on text similarity.

Cross-lingual embeddings may assist review, but they are not definitive proof of contamination or independence.

---

# 19. Leakage Prevention Strategy

Before training:

```text
1. Keep evaluation sources physically/logically separate.
2. Track source provenance.
3. Check exact normalized overlap.
4. Check near-duplicates.
5. Check translated/cross-lingual variants.
6. Check source/group overlap.
7. Search benchmark-specific phrases and IDs.
8. Manually inspect suspicious matches.
```

For important experiments, use multiple complementary methods.

---

# 20. Exact Duplicate Detection

Useful normalization may include:

```text
Unicode normalization
trim whitespace
collapse repeated whitespace
normalize line endings
```

Do not normalize so aggressively that genuinely different examples become identical.

Track duplicate counts and rates.

---

# 21. Near-Duplicate Detection

Possible methods include:

```text
n-gram similarity
MinHash
edit similarity
embeddings
semantic clustering
```

No method should automatically define semantic identity.

Embedding similarity in particular can collapse examples that look semantically similar while differing in important details.

Examples:

```text
same math template with different numbers
same code skeleton with different bugs
similar questions with opposite conditions
```

Therefore:

> Use similarity systems to identify candidates for review, not as an automatic deletion oracle.

Thresholds should be validated on the actual dataset.

---

# 22. Cross-Split Deduplication

Always check:

```text
train ↔ validation
train ↔ test
validation ↔ test
```

Cross-split duplication can invalidate evaluation.

---

# 23. Split Strategy

Typical roles:

```text
train
→ gradient updates

validation
→ model/config/checkpoint decisions

test
→ final evaluation
```

Repeatedly optimizing decisions against the test set turns it into development data.

---

# 24. Group-Level Splitting

Random row-level splitting is unsafe when examples share an underlying source.

Examples:

```text
multiple questions from one document
functions from one repository
turns from one conversation
paraphrases from one source question
multiple translations of one canonical item
```

In such cases split by:

```text
document
repository
conversation
canonical source
group ID
```

The unit of independence matters more than the row.

---

# 25. Manual Inspection Has Two Different Goals

Do not confuse qualitative inspection with statistical auditing.

## Qualitative sanity review

Useful for discovering obvious structural problems:

```text
20–50 representative samples
```

can reveal:

```text
bad formatting
wrong roles
unnatural teacher style
broken schema
obvious language problems
```

This does **not** estimate dataset error rate reliably.

## Statistical quality audit

If the goal is to estimate or detect an error rate, choose sample size from the statistical objective.

For example, if we assume a true critical-error rate `p` and want probability `c` of observing at least one error:

```text
n ≥ log(1 - c) / log(1 - p)
```

For approximately:

```text
p = 5%
confidence of seeing ≥1 error = 95%
```

we need roughly:

```text
n ≈ 59
```

For estimating an error proportion with a confidence interval, use an appropriate proportion sample-size calculation instead.

---

# 26. Stratified Review

Pure random review may miss rare but important categories.

Include stratified inspection across:

```text
capability category
source
teacher model
difficulty
length bucket
language/register
generation method
```

Also inspect:

```text
shortest samples
longest samples
high-similarity clusters
validation warnings
rare categories
```

The review plan should reflect dataset risk.

---

# 27. Manual Quality Questions

For each reviewed sample ask:

```text
Is the prompt correct?

Is the response correct?

Are the roles correct?

Is the language natural?

Does it teach the intended capability?

Is it ambiguous?

Is it unnecessarily verbose?

Does it contain unsupported claims?

Could it originate from evaluation data?

Would we want the model to imitate this?
```

That final question is fundamental to SFT.

---

# 28. Reject Bad Samples

Remove or repair examples containing:

```text
wrong targets
empty targets
broken formatting
wrong language
garbled text
evaluation contamination
severe ambiguity
unwanted behavior
invalid code where correctness matters
```

Do not retain bad data merely to preserve dataset size.

---

# 29. Difficulty and Distribution

Track difficulty if the task provides a defensible definition.

Possible:

```text
easy
medium
hard
```

Do not fabricate difficulty labels merely to populate metadata.

Check category imbalance, but do not automatically force equal distributions.

The intended deployment distribution may itself be imbalanced.

---

# 30. Data Quality vs Quantity

Do not assume:

```text
10k examples > 2k examples
```

Useful experiments may compare:

```text
2k curated
vs
10k broader/noisier
```

Dataset size is itself an experimental variable.

---

# 31. Count Tokens, Not Only Samples

Two 5,000-sample datasets may have radically different training scale.

Track where practical:

```text
sample count
total tokens
input/context tokens
target/trainable tokens
```

For assistant-only loss, **trainable target-token count** can be especially informative.

---

# 32. Sequence-Length Statistics

Before selecting context length calculate:

```text
median
P90
P95
P99
maximum
```

for:

```text
input length
target length
total length
```

Use these to estimate:

```text
truncation
memory requirements
training cost
```

---

# 33. Truncation Must Be Measured

Record:

```text
number truncated
percentage truncated
tokens removed
which portion was removed
```

IF target content is frequently truncated:

```text
→ reconsider max sequence length
→ shorten/restructure examples
→ split examples when appropriate
```

Do not silently train on systematically incomplete answers.

---

# 34. Chat Template Policy

Store raw semantic messages whenever possible.

Apply the model's actual chat template at training/preprocessing time.

For each experiment pin:

```text
tokenizer/model revision
chat template revision or content
template-related configuration
```

Do not assume the same raw dataset produces identical token sequences under different tokenizer/template revisions.

Before training, inspect:

```text
raw messages
↓
rendered text
↓
tokens
↓
labels
```

---

# 35. BOS, EOS and End-of-Turn Tokens

Validate all relevant boundary tokens.

Check:

```text
BOS
EOS
end-of-turn tokens
assistant start/end markers
```

Questions:

```text
Is BOS required?

Is it missing?

Is it duplicated?

Does apply_chat_template already add it?

Is EOS/end-of-turn added exactly where expected?

Does later tokenization add another special-token layer?
```

A common failure is:

```text
apply_chat_template(..., tokenize=False)
↓
tokenizer(..., add_special_tokens=True)
```

when the rendered template already contains necessary special tokens.

Always inspect the resulting token stream.

---

# 36. Multi-Turn Label Masking

Loss policy must be intentional.

For assistant-only SFT:

```text
System       → ignore
User 1       → ignore
Assistant 1  → TRAIN
User 2       → ignore
Assistant 2  → TRAIN
```

unless the experiment explicitly chooses another policy.

Verify every intended assistant span.

Do not assume framework defaults.

---

# 37. Valid Training Tokens

Count how many tokens actually contribute to loss per sample.

IF:

```text
valid target tokens = 0
```

then the sample cannot teach the intended output.

Reject or repair it.

IF many samples have very few trainable tokens:

```text
→ inspect masking
→ inspect truncation
→ inspect role/template parsing
```

---

# 38. Padding

Verify:

```text
attention masks
label masks
pad token
padding side where relevant
```

`pad_token_id == eos_token_id` is not automatically wrong.

The important question is whether padded positions are handled correctly and excluded from the objective when required.

---

# 39. Packing and Sample Isolation

Packing can improve utilization by combining short examples.

But packed examples must preserve sample boundaries correctly.

Verify:

```text
EOS/end-of-turn boundaries
position handling
attention boundaries
label masking
sample reconstruction
```

Do not assume inserting EOS alone always provides attention isolation.

If the training method/framework uses boundary-aware or block-diagonal attention, verify that it is actually active.

For architectures where standard position-ID tricks do not provide sufficient isolation, use the framework's supported boundary-aware collator/masking mechanism.

IF sample-isolation behavior is unclear:

```text
→ disable packing
→ establish correctness first
```

Do not sacrifice training semantics merely for throughput.

---

# 40. Tool-Calling Token Validation

For tool datasets, inspect rendered/tokenized examples and verify:

```text
tool definitions appear where expected

assistant tool calls are trainable

tool arguments remain valid structured data

tool responses are context rather than accidental targets

final assistant response has correct loss policy

tool-call IDs/names survive preprocessing
```

Validate tool arguments against JSON/schema constraints when possible.

---

# 41. Preference Dataset Validation

For each preference example verify:

```text
shared prompt is correct
chosen and rejected answer the same task
chosen is genuinely preferred
rejected is plausible enough to teach something
neither branch contains accidental leakage
```

After templating/tokenization verify the common prompt construction.

Do not let formatting differences accidentally become the preference signal.

---

# 42. Automated Validation

Reusable validators should check:

```text
required fields
allowed roles
non-empty content
duplicate IDs
exact duplicates
cross-split overlap
language where applicable
length limits
JSON/schema validity
valid target-token counts
benchmark/source overlap
tool-call validity
```

Critical failures should stop the pipeline.

---

# 43. Validation Severity

## Error

Training should not continue.

Examples:

```text
missing target
invalid conversation structure
train/test duplicate
confirmed benchmark contamination
zero valid target tokens
invalid tool-call schema
```

## Warning

Requires inspection.

Examples:

```text
very long sample
language anomaly
near duplicate
rare category
unusual target length
```

## Info

Statistics such as:

```text
sample count
token count
length percentiles
category distribution
source distribution
```

---

# 44. Dataset Validation Report

Every material dataset version should produce a machine-readable report.

Example:

```json
{
  "samples": 5000,
  "train": 4500,
  "validation": 250,
  "test": 250,
  "duplicates": 0,
  "cross_split_duplicates": 0,
  "zero_target_token_samples": 0,
  "truncated_at_2048": 41,
  "median_tokens": 440,
  "p95_tokens": 1380
}
```

Values must come from actual validation.

Never invent them.

---

# 45. Version the Dataset Artifact

Material changes require a new traceable revision.

Examples:

```text
samples added/removed
labels corrected
filtering changed
deduplication changed
split changed
category distribution changed
generation process changed
```

Experiments should reference exact immutable revisions where possible.

Example:

```yaml
dataset:
  repo: cbarkinozer/turkish-sft
  revision: "<commit-hash>"
```

Avoid relying only on:

```text
main
latest
```

---

# 46. Version the Dataset-Building Code Too

The dataset artifact alone is not sufficient for full reproducibility.

Record:

```text
dataset artifact revision
+
Git commit of generation/preprocessing code
+
source revisions
+
generation configuration
```

Where possible preserve:

```text
scraping scripts
generation scripts
filtering scripts
deduplication configuration
split-generation code
```

The objective is to be able to explain not only:

```text
Which dataset did we use?
```

but also:

```text
How was that dataset produced?
```

---

# 47. Dataset Manifest

A published or experiment-critical dataset should have a manifest containing information such as:

```yaml
dataset:
  repo: cbarkinozer/turkish-sft
  revision: "<hf-commit>"

builder:
  git_commit: "<repo-commit>"

sources:
  - name: "..."
    revision: "..."

generation:
  provider: "..."
  model: "..."
  seed: 42
  deterministic: false
```

The schema may evolve.

The goal is traceability.

---

# 48. Dataset Card

Published datasets should document:

```text
purpose
target capability
schema
language
size
source/provenance
generation process
filtering
deduplication
split strategy
licenses/usage restrictions
known limitations
intended use
out-of-scope use
```

Synthetic generation should be disclosed.

---

# 49. Historical Dataset Revisions

Once an experiment references a dataset revision, treat that revision as immutable.

If data changes:

```text
→ create a new revision
→ update experiment references
→ create a new experiment when the effective training data changed materially
```

Do not silently replace historical data.

---

# 50. Common Failure — Formatting Improves, Capability Does Not

Symptoms:

```text
JSON validity ↑
answer style ↑
task accuracy ≈
```

Check:

```text
Are examples too templated?

Do examples genuinely require the desired capability?

Are answers trivially predictable?

Is difficulty sufficient?

Is task diversity sufficient?
```

The dataset may be teaching form rather than capability.

---

# 51. Common Failure — Model Memorizes Patterns

Symptoms:

```text
training performance very high
validation weak
responses repetitive
```

Check:

```text
duplicates
near-duplicates
template diversity
training duration
effective dataset diversity
```

---

# 52. Common Failure — Model Becomes Too Verbose

First distinguish:

```text
useful task reasoning
```

from:

```text
unwanted conversational verbosity
```

Possible causes:

```text
teacher is verbose
every target contains long explanations
response-length distribution is skewed
boilerplate is repeated
```

If concise answers are desired, include high-quality concise targets.

Do not remove useful reasoning merely because responses are long.

---

# 53. Common Failure — Model Becomes Too Narrow

If:

```text
target capability ↑
supporting capability ↓ significantly
```

check whether the training distribution is too narrow.

Possible response:

```text
add supporting-capability examples
mix broader high-quality data
reduce training intensity
```

Only preserve capabilities required by the experiment's capability budget.

Specialization may intentionally sacrifice unrelated capabilities.

---

# 54. Common Failure — Benchmark Improves Suspiciously Much

IF improvement is unexpectedly large:

```text
→ investigate contamination before celebrating
```

Check:

```text
exact overlap
near duplicates
translated benchmark items
shared source IDs
same underlying canonical problems
synthetic benchmark derivatives
answer leakage
evaluation bugs
```

Large improvements can be real, but contamination should be ruled out first.

---

# 55. Dataset Decision Rules

```text
IF exact cross-split duplicates exist:
→ STOP
→ rebuild the affected splits
```

```text
IF benchmark-derived samples are found:
→ STOP
→ remove them
→ repeat contamination checks
```

```text
IF many targets are truncated:
→ reconsider context length or sample construction
```

```text
IF many samples have no valid training tokens:
→ fix masking/tokenization before training
```

```text
IF synthetic outputs are repetitive:
→ improve generation diversity
→ vary prompts/sources/teachers
→ filter redundant patterns
```

```text
IF embedding deduplication proposes large deletion clusters:
→ manually validate clusters
→ do not auto-delete purely by cosine threshold
```

```text
IF packed samples can attend across unrelated examples unexpectedly:
→ fix boundary handling or disable packing
```

```text
IF tool outputs contribute to loss unintentionally:
→ fix role-aware masking before training
```

---

# 56. Before Creating a Dataset Version

Check:

```text
□ Target capability is defined.

□ Capability taxonomy exists.

□ Dataset schema is explicit.

□ Multi-turn/tool structure is defined if relevant.

□ Loss policy is defined.

□ Data sources are traceable.

□ Licensing and usage terms were reviewed.

□ Synthetic provider terms were reviewed where applicable.

□ Synthetic-generation metadata is preserved.

□ Exact duplicates were checked.

□ Near duplicates were reviewed.

□ Cross-split duplicates were checked.

□ Cross-lingual benchmark leakage was considered.

□ Group-level leakage was considered.

□ Category/source distributions were inspected.

□ Qualitative review was performed.

□ Statistical audit was performed when required.

□ Token-length statistics were calculated.

□ Truncation was measured.

□ Chat-template rendering was inspected.

□ BOS/EOS/end-of-turn behavior was checked.

□ Label masking was validated.

□ Tool/reasoning fields were validated if relevant.

□ Packing semantics were validated if enabled.

□ Zero-target-token samples were rejected/fixed.

□ Validation report exists.
```

---

# 57. Before Using a Dataset in Training

Check:

```text
□ Exact dataset revision is pinned.

□ Dataset-building Git commit is known.

□ Validation passed.

□ Train/validation/test roles are clear.

□ Evaluation data is excluded.

□ Chat template matches the target model.

□ Raw → rendered → tokenized representations were inspected.

□ Multi-turn masking policy is correct.

□ Sequence-length decision is justified.

□ Packing was validated if enabled.

□ Sample and trainable-token counts are known.

□ Experiment config points to the intended revision.
```

---

# 58. Before Publishing a Dataset

Check:

```text
□ Dataset card exists.

□ Provenance is documented.

□ Licenses and provider restrictions are documented.

□ Publication rights were checked.

□ Sensitive/private material was reviewed.

□ Benchmark contamination was checked.

□ Schema is documented.

□ Splits are documented.

□ Synthetic generation is disclosed.

□ Known limitations are documented.

□ Dataset artifact revision is traceable.

□ Generation/build code revision is traceable.
```

---

# 59. Agent Rules

```text
IF creating a dataset:
→ define target capability first
→ define capability categories
→ define the training schema and loss policy
→ preserve provenance
```

```text
IF adding external data:
→ verify license and usage terms
→ do not assume public means reusable
```

```text
IF using an external model/API to generate synthetic data:
→ verify current provider terms first
→ record provider/model/configuration
→ record seed if supported
→ acknowledge nondeterminism where applicable
```

```text
IF generating synthetic data:
→ never use evaluation questions as generation seeds
→ teach the underlying skill instead
```

```text
IF multilingual evaluation is involved:
→ check canonical/source-level contamination across languages
→ do not rely only on lexical similarity
```

```text
IF storing conversational data:
→ preserve model-independent semantic messages where possible
→ apply model-specific templates later
```

```text
IF using multi-turn SFT:
→ explicitly define which assistant turns contribute to loss
→ verify the resulting labels
```

```text
IF using tool calling:
→ preserve tool calls and tool responses structurally
→ train only on outputs the model is expected to generate
```

```text
IF packing:
→ verify sample-boundary attention behavior
→ disable packing if isolation cannot be guaranteed
```

```text
IF a material dataset change occurs:
→ create a new dataset revision
→ update experiment references
→ create a new experiment when training data materially changes
```

---

# 60. Final Principle

The objective is not to collect the most data.

The objective is to construct data that teaches the intended behavior while allowing us to explain exactly why the model changed.

A good dataset should let us answer:

```text
What did we teach?

Why did we teach it?

What behavior actually contributes to loss?

Where did the data come from?

Were we allowed to use it?

What did we exclude?

How did we protect evaluation integrity?

How was the data validated?

Can we regenerate it?

What changed between revisions?
```

The dataset is not merely an input file.

It is part of the experiment.
