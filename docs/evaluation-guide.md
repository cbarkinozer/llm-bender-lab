# Evaluation Guide

This document defines how models are evaluated inside `llm-bender-lab`.

Its purpose is to answer:

> Did fine-tuning improve the intended capability, what did it change elsewhere, and are those trade-offs acceptable?

Evaluation should be:

* comparable,
* reproducible,
* task-relevant,
* resistant to leakage,
* explicit about uncertainty,
* and representative of the artifact that will actually be deployed.

For training decisions, see `finetuning-playbook.md`.

For experiment structure, see `experiment-guide.md`.

For dataset and contamination rules, see `dataset-guide.md`.

For complete traceability requirements, see `reproducibility.md`.

---

# Part I — Evaluation Design and Protocol Freezing

## 1. Evaluate Capability, Not Training Success

Training is not successful merely because:

```text
training loss decreased
```

or:

```text
training completed
```

The relevant question is whether the resulting model improved on the intended task.

Default workflow:

```text
Define Target
↓
Define Evaluation
↓
Measure Starting Model
↓
Freeze Protocol
↓
Fine-tune
↓
Evaluate Candidate
↓
Measure Regressions
↓
Inspect Outputs
↓
Decide
```

---

## 2. Define Evaluation Before Training

Before training, define:

```text
target capability
primary metric
supporting capabilities
regression metrics
capability budget
evaluation datasets
generation protocol
```

Do not train first and later search for metrics where the model happens to look better.

---

## 3. Three Evaluation Layers

Separate metrics into:

### Target capabilities

What we explicitly want to improve.

Examples:

```text
Turkish capability
tool-call accuracy
unit-test generation
structured output
```

### Supporting capabilities

Capabilities required for the specialization to remain useful.

Examples:

```text
instruction following
format correctness
basic reasoning
argument extraction
stopping behavior
```

### Non-target capabilities

Capabilities worth monitoring but which may be allowed to regress.

Examples:

```text
English QA
general knowledge
unrelated coding
broad reasoning
```

Do not treat every regression equally.

---

## 4. Capability Budget

Define acceptable trade-offs before training.

Example:

```yaml
capability_budget:
  turkish_target:
    goal: improve

  instruction_following:
    max_regression: 2.0

  json_validity:
    max_regression: 0.0

  general_reasoning:
    max_regression: 5.0
```

A specialist model may intentionally lose unrelated capabilities.

The loss must still be measured and understood.

---

## 5. Define the Starting Model Precisely

Use **starting model** when possible instead of ambiguously saying `base model`.

There are two different cases.

### Starting from an instruct/chat model

Example:

```text
Qwen-Instruct
↓
specialized Qwen-Instruct
```

The original instruct model is the natural baseline.

Its prompt and chat format can usually remain consistent after fine-tuning.

### Starting from a raw foundation model

Example:

```text
Llama-Base
↓
instruction-tuned specialist
```

The raw model may require completion-style or few-shot prompting, while the fine-tuned model may use chat formatting.

In this case exact prompt serialization parity may be impossible.

The comparison should instead preserve:

```text
same semantic task
same evaluation items
appropriate prompting for each model type
same scoring criteria
```

Document the difference explicitly.

Do not force an instruct chat template onto a raw foundation model merely for superficial parity.

---

## 6. Measure the Starting Model First

Before training, record:

```text
model revision
tokenizer revision
chat template
evaluation dataset revision
prompt protocol
generation config
evaluation code revision
raw outputs where useful
aggregate metrics
```

Never reconstruct this baseline from memory after training.

---

## 7. Freeze the Evaluation Protocol

Record all settings that can materially affect results:

```text
benchmark version
item IDs
prompt template
system prompt
few-shot examples
chat template
thinking mode
temperature
top_p
top_k
max_new_tokens
stop conditions
seed where meaningful
evaluation batch size
padding side
padding strategy
inference backend
precision
scoring implementation
```

Infrastructure settings are part of the evaluation protocol when they can change outputs.

---

## 8. Semantic Parity Over Raw-String Parity

For models from different families, use each model's correct native template.

Aim for:

```text
same semantic instruction
```

not necessarily:

```text
identical serialized token string
```

Record any model-specific adaptation.

---

## 9. Batch Size and Padding

Inference batching can alter model behavior in some implementations.

Therefore comparative evaluation should keep consistent where practical:

```text
batch size
padding side
padding token
padding strategy
inference backend
```

If changing them changes outputs materially:

```text
→ investigate
→ document the sensitivity
→ use a fixed canonical setting for reported comparisons
```

Do not assume batch-size changes are always numerically irrelevant.

---

## 10. Deterministic and Stochastic Evaluation

Deterministic decoding is useful when appropriate.

Examples:

```text
classification
exact-answer QA
structured output
tool selection
```

However, do not force greedy decoding merely because it is reproducible.

Use the model's recommended evaluation protocol when one exists.

IF greedy decoding produces pathological behavior not representative of intended use:

```text
→ use a documented low-temperature or recommended sampling setup
→ keep it identical across compared models
→ use repeated samples where stochasticity matters
```

A fixed seed can improve repeatability but does not guarantee full determinism across every backend or API.

---

# Part II — Benchmark Selection and Integrity

## 11. Select Benchmarks to Answer Questions

For every benchmark ask:

```text
What capability does it measure?
Why does that capability matter?
Is it target, supporting, or regression?
Can we reproduce the protocol?
Is contamination controlled?
```

Do not run every benchmark merely because it appears on a model card.

---

## 12. Model-Card Scores Are References

Same benchmark name does not imply identical experimental conditions.

Scores may differ because of:

```text
prompting
few-shot setup
thinking mode
generation parameters
benchmark revision
harness implementation
model revision
```

Treat published scores as references unless their protocol is reproduced closely.

---

## 13. Pin Benchmark Versions

Record when possible:

```text
dataset revision
Git commit
release tag
package version
item IDs
```

Avoid mutable identifiers such as:

```text
latest
main
current
```

for final reported results.

---

## 14. Protect Evaluation Integrity

Before evaluation:

```text
→ check training/evaluation separation
→ check exact overlaps
→ check near-duplicates
→ check source overlap
→ check translated benchmark variants
→ check synthetic derivatives
```

If contamination is found:

```text
→ invalidate affected results
→ document the problem
→ rebuild or replace the evaluation set
```

---

## 15. Repeated Test Use

The test set should not become another development benchmark.

Use:

```text
train
development / validation
final test
```

for different purposes.

IF repeated experiment choices are based on the test set:

```text
→ treat that set as development data
→ introduce a fresh holdout for final evaluation
```

---

## 16. Benchmark Overfitting Without Leakage

A model can overfit to a benchmark through repeated experiment iteration even without literal training contamination.

Warning signs:

```text
benchmark score ↑
real usage ≈
related independent benchmark ≈
manual quality ≈
```

Respond with:

```text
independent holdouts
related benchmarks
realistic deployment examples
robustness tests
```

---

# Part III — Metrics, Parsing and Scoring

## 17. Use Task-Relevant Metrics

Examples:

### Classification

```text
accuracy
precision
recall
F1
```

### Structured output

```text
parse success
schema validity
field accuracy
task success
```

### Tool calling

```text
tool selection
argument accuracy
schema validity
execution success
end-to-end success
```

### Code

```text
compile success
execution success
unit-test success
Pass@k
```

### Unit-test generation

```text
execution success
non-trivial assertions
coverage
mutation score
```

Prefer metrics close to actual use.

---

## 18. Separate Capability From Formatting

A fine-tuned model may learn to satisfy the evaluator's expected format without becoming more capable.

Example:

```text
Base:
"The answer is 42."

Fine-tuned:
<answer>42</answer>
```

If the evaluator only recognizes `<answer>...</answer>`, the second model may receive credit while the first does not.

This is **parser overfitting**.

Always distinguish:

```text
answer correctness
format compliance
parser success
```

---

## 19. Robust Answer Extraction

Before exact-match scoring, define how the final answer is extracted.

Prefer task-appropriate extraction such as:

```text
structured parser
robust deterministic normalization
validated answer pattern
task-specific parser
```

LLM-assisted extraction may be used when deterministic parsing is genuinely insufficient, but then the extractor itself becomes part of the evaluation protocol and must be versioned.

Do not silently change extraction rules between models.

---

## 20. Parser Diagnostics

Track separately where useful:

```text
semantic answer correct?
parser succeeded?
required format satisfied?
```

IF:

```text
fine-tuned parser success ↑↑
semantic correctness ≈
```

then the improvement is primarily formatting, not underlying capability.

That may still be useful, but report it correctly.

---

## 21. Exact Match Normalization

Define transformations explicitly.

Possible:

```text
whitespace normalization
case normalization
Unicode normalization
numeric-format normalization
limited punctuation normalization
```

Do not normalize incorrect answers into correct ones.

Keep raw outputs for auditability.

---

## 22. Structured-Output Evaluation

Evaluate progressively:

```text
generation completed
↓
parseable
↓
schema-valid
↓
fields correct
↓
task successful
```

This separates structural from semantic failure.

---

## 23. Tool-Calling Evaluation

Evaluate independently:

```text
tool selection
argument schema
argument values
call ordering
tool-result use
final answer
end-to-end success
```

End-to-end success is usually the strongest metric when executable evaluation is feasible.

---

## 24. Multi-Turn Evaluation

If deployment is conversational, test:

```text
context retention
follow-up behavior
role handling
tool-result integration
instruction persistence
```

Single-turn improvement does not guarantee multi-turn improvement.

---

## 25. Stopping and Repetition

Measure:

```text
max_new_tokens hit rate
repetition loops
missing termination
garbage after correct answer
```

A model that answers correctly but routinely fails to stop has regressed.

---

# Part IV — Human and LLM-Based Evaluation

## 26. Manual Qualitative Evaluation

Inspect representative outputs for:

```text
correctness
naturalness
instruction following
verbosity
repetition
hallucination
format
style drift
stopping
refusal behavior
```

A set such as 30–100 prompts may be useful for qualitative inspection, but it is not automatically a statistical estimate of population quality.

---

## 27. Blind Comparisons

When practical:

```text
Model A
Model B
```

instead of exposing model identity.

Randomize A/B order.

This reduces expectation bias.

---

## 28. Pairwise Evaluation

Use explicit criteria.

Example:

```text
correctness
instruction following
relevance
clarity
```

Allow:

```text
A
B
Tie
```

Avoid an undefined "which is better?" when more precise rubrics are possible.

---

## 29. Response-Length Bias

Humans and automated judges may prefer longer answers even when additional text adds little value.

Always track:

```text
average output tokens
median output tokens
length distribution
```

alongside preference/win-rate results.

IF the winning model is substantially more verbose:

```text
→ inspect whether wins come from additional useful information
→ inspect matched-length examples
→ consider reporting win rates by response-length bucket
```

Do not automatically conclude:

```text
longer answer = better model
```

A formal "length-adjusted win rate" may be useful in research settings, but it is not mandatory for every experiment.

---

## 30. LLM-as-a-Judge

Record:

```text
judge provider
judge model/revision
judge prompt
temperature
rubric
response ordering
```

Where practical:

```text
randomize A/B order
allow ties
retain raw judgments
test consistency
human-review disagreements
```

Treat the judge as a measurement instrument, not ground truth.

---

## 31. Judge Origin / Family Bias

If synthetic training data was generated primarily by one model family, using the same family as the sole judge can create a risk of stylistic self-preference.

Example:

```text
Teacher:
Model family A

Judge:
Model family A
```

This does not automatically invalidate the evaluation, but it weakens independence.

For important subjective evaluations, prefer one of:

```text
a judge from an independent model family
multiple heterogeneous judges
human validation of a representative subset
task-verifiable metrics where available
```

Do **not** impose cross-family judging as an absolute rule.

What matters is recognizing and reducing dependence between:

```text
training-data generator
candidate model style
evaluation judge
```

---

## 32. Judge Biases

Potential biases:

```text
position bias
verbosity bias
style bias
self/family preference
format preference
reference-answer bias
```

Mitigate with:

```text
order swapping
blinding
structured rubrics
multiple judges
human checks
```

---

## 33. Human Evaluation

Define a rubric before scoring.

Examples:

```text
pass / partial / fail
```

or:

```text
0 = incorrect
1 = partially correct
2 = correct
```

Do not alter the rubric after seeing model identities or desired outcomes.

---

## 34. Inter-Rater Agreement

For important multi-rater evaluations, consider:

```text
raw agreement
Cohen's kappa
Krippendorff's alpha
```

Choose according to the rating design.

Do not report post-adjudication agreement as though it were independent initial agreement.

---

# Part V — Statistics and Regression Analysis

## 35. Report Uncertainty

Point estimate:

```text
accuracy = 61%
```

is less informative than an estimate with uncertainty.

For binary metrics, Wilson confidence intervals are often useful.

Use uncertainty especially when:

```text
datasets are small
differences are small
model selection depends on the result
```

---

## 36. Use Paired Comparisons When Data Is Paired

When both models answer the same items, consider paired methods such as:

```text
McNemar
paired bootstrap
permutation tests
```

Do not discard pairing information.

---

## 37. Effect Size Matters

Statistical significance is not practical significance.

Always ask:

```text
How much better?
Does it matter?
What regressions did it cost?
What compute did it cost?
```

---

## 38. Multiple Comparisons

When making many formal statistical tests, consider appropriate controls such as:

```text
Holm
Benjamini-Hochberg
```

Use them when the analysis genuinely requires inferential control.

Do not apply corrections mechanically to informal exploratory work.

---

## 39. Regression Table

For important capabilities record:

| Capability            | Start | Fine-tuned | Delta |  Budget | Status |
| --------------------- | ----: | ---------: | ----: | ------: | ------ |
| Target Turkish        |    44 |         58 |   +14 | improve | PASS   |
| Instruction following |    52 |         51 |    -1 |      -2 | PASS   |
| General reasoning     |    30 |         26 |    -4 |      -5 | PASS   |
| JSON validity         |    98 |         98 |     0 |       0 | PASS   |

---

## 40. Specialist Models

General loss is not automatically failure.

A specialist may intentionally trade:

```text
English ability
broad knowledge
unrelated tasks
```

for:

```text
Turkish specialization
tool calling
code specialization
```

The trade-off must remain within the intended deployment requirements.

---

## 41. Slice Analysis

Aggregate metrics can hide failures.

Slice by relevant attributes:

```text
capability
difficulty
source
language/register
input length
output length
tool type
domain
```

Example:

```text
overall score ↑
hard reasoning ↓
```

may change the conclusion.

---

## 42. Error Taxonomy

Examples for tool calling:

```text
wrong tool
missing argument
wrong value
invalid structure
unnecessary tool call
final-answer failure
```

Examples for QA:

```text
knowledge error
reasoning error
instruction error
format error
hallucination
```

Track error types when aggregate metrics are insufficient.

---

# Part VI — Checkpoint and Artifact Evaluation

## 43. Checkpoint Selection

Do not assume the final checkpoint is best.

Compare candidate checkpoints using:

```text
target metrics
supporting metrics
regressions
qualitative behavior
```

---

## 44. Validation Loss Is Not the Final Objective

For generative tasks:

```text
minimum validation loss
```

may not correspond to:

```text
best task behavior
```

Prefer the metric that most closely represents intended use.

---

## 45. Record Selection Policy

Store:

```text
candidate checkpoints
selection metric
capability budget
selected checkpoint
selection reason
```

---

## 46. Adapter vs Merged Model

If LoRA is used, evaluate both when the merged model will be deployed.

```text
Base + Adapter
```

and:

```text
Merged Model
```

should be expected to behave similarly, but do not assume they are identical.

IF merged performance drops materially:

```text
→ verify merge implementation
→ verify adapter scaling
→ verify base revision
→ verify dtype/precision
→ verify save/load path
```

In particular inspect mismatches such as:

```text
trained/evaluated in BF16
but merged or reloaded in FP16
```

or unintended lower-precision conversion.

Do not blame fine-tuning until the artifact conversion path is verified.

---

## 47. Quantization Evaluation

If deployment uses:

```text
GGUF
AWQ
GPTQ
MLX quantization
KV-cache quantization
```

evaluate the actual quantized deployment artifact.

Record:

```text
pre-quantization
post-quantization
delta
```

---

## 48. Serving-Stack Evaluation

Different runtimes can change:

```text
sampling
stop handling
precision
chat templating
KV-cache behavior
```

Examples:

```text
Transformers
vLLM
TGI
llama.cpp
MLX
```

Run a deployment-level validation when production differs from development.

---

## 49. Long-Context Regression

Fine-tuning or deployment conversion can degrade long-context behavior even when short benchmarks improve.

If long-context capability matters to intended use, include regression tests such as:

```text
long-context retrieval
needle-in-a-haystack style tests
multi-document QA
long-conversation retention
```

Test at representative context lengths, for example:

```text
short
medium
near deployment maximum
```

Do not require long-context testing when the specialist is intentionally limited to short contexts.

The test belongs in the capability budget only when long-context behavior matters.

---

## 50. KV-Cache / Deployment Context Checks

If production uses KV-cache quantization or a materially different serving configuration:

```text
→ test long-context behavior under that actual configuration
```

A model passing long-context tests in development precision does not prove the production runtime preserves that behavior.

---

## 51. Latency and Throughput

For deployment candidates measure as relevant:

```text
time to first token
tokens/sec
requests/sec
VRAM
concurrency
```

The highest benchmark score is not automatically the best production model.

---

# Part VII — Development, Final Evaluation and Robustness

## 52. Development vs Final Evaluation

A useful pattern:

```text
small dev evaluation
↓
fast experiment iteration
↓
candidate selection
↓
full final evaluation
```

Do not report development-subset results as final benchmark scores.

---

## 53. Fixed Evaluation Subsets

If using subsets:

```text
→ choose deterministically
→ record item IDs
→ reuse the same subset
```

Do not choose a different convenient subset for each model.

---

## 54. Robustness Evaluation

For selected candidates, consider:

```text
prompt paraphrases
typos
format variations
longer context
different instruction wording
```

This helps detect brittle benchmark-specific learning.

---

## 55. Out-of-Distribution Checks

When useful:

```text
train:
formal Turkish

OOD:
colloquial Turkish
```

or:

```text
train:
known tool schemas

OOD:
unseen structurally similar tools
```

This helps distinguish real capability from memorized patterns.

---

## 56. Thinking vs Non-Thinking Modes

Record reasoning mode explicitly.

Do not compare:

```text
starting model thinking mode
```

against:

```text
fine-tuned model non-thinking mode
```

unless intentional.

---

## 57. Reasoning Evaluation

Do not require generated reasoning text to match a reference rationale exactly.

Prefer:

```text
final correctness
task success
verifiable intermediate constraints
```

If rationale quality itself matters, define a separate rubric.

---

# Part VIII — Suspicious Results and Failure Diagnosis

## 58. Suspiciously Large Improvement

IF improvement is unexpectedly large:

```text
→ check contamination
→ check translated benchmark overlap
→ check parser behavior
→ check scoring
→ check prompt parity
→ check generation config
→ check benchmark version
```

Do not celebrate before validating the measurement.

---

## 59. Large Regression

IF an unrelated capability collapses:

```text
→ verify evaluation first
```

Check:

```text
adapter loading
wrong checkpoint
chat template
generation config
precision
quantization
benchmark revision
```

Only then investigate catastrophic forgetting.

---

## 60. Formatting Gain vs Capability Gain

IF:

```text
parser success ↑
format validity ↑
task correctness ≈
```

report:

```text
formatting improvement
```

not:

```text
capability improvement
```

unless independent evidence supports it.

---

## 61. Preference Win With Much Longer Outputs

IF:

```text
fine-tuned win rate ↑
average response length ↑↑
```

then:

```text
→ inspect matched-length examples
→ inspect whether additional content is actually useful
→ report length statistics with the win rate
```

Treat verbosity as a possible confounder.

---

## 62. Judge and Teacher Are Closely Related

IF the same provider/model family generated much of the training data and performs judging:

```text
→ flag possible origin/style bias
→ validate with an independent judge or humans when the result matters
```

Do not automatically discard the result, but do not treat the judge as fully independent evidence either.

---

# Part IX — Result Storage and Comparability

## 63. Machine-Readable Results

Example:

```json
{
  "experiment_id": "exp-003-lr-1e-4",
  "model_revision": "...",
  "checkpoint": "checkpoint-1200",
  "evaluation_config": "turkish-v1",
  "metrics": {
    "turkish_target": 58.2,
    "instruction_following": 51.7,
    "general_reasoning": 26.1
  }
}
```

Store raw counts where relevant.

---

## 64. Per-Item Results

Where practical retain:

```text
item ID
prompt
output
reference
parsed answer
score
error type
metadata
```

This allows later:

```text
paired analysis
re-scoring
parser auditing
slice analysis
regression inspection
```

---

## 65. Version Evaluation Configurations

Example:

```text
configs/evaluation/
├── turkish-v1.yaml
├── tool-calling-v1.yaml
└── regression-v1.yaml
```

Material changes create a new version.

Examples:

```text
prompt changed
parser changed
few-shot examples changed
benchmark changed
judge changed
generation config changed
```

---

## 66. Comparability Rule

Two scores are directly comparable only when relevant conditions are compatible.

Check:

```text
evaluation items
benchmark revision
semantic prompt
task mode
generation configuration
parser/scorer
serving conditions where material
```

If they differ materially:

```text
→ label comparison approximate or invalid
```

---

# Part X — Checklists

## 67. Before Running Evaluation

* [ ] Evaluation goal is defined.
* [ ] Benchmark role is target/supporting/regression.
* [ ] Benchmark revision is pinned.
* [ ] Evaluation contamination was checked.
* [ ] Prompt protocol is frozen.
* [ ] Chat-template behavior is correct.
* [ ] Generation config is frozen.
* [ ] Batch size and padding strategy are recorded.
* [ ] Thinking mode is recorded if relevant.
* [ ] Parsing/extraction logic is tested.
* [ ] Scoring implementation is tested.
* [ ] Starting and fine-tuned conditions are comparable.
* [ ] Per-item results will be retained where useful.

---

## 68. Before Comparing Two Models

* [ ] Same evaluation items are used.
* [ ] Same benchmark revision is used.
* [ ] Semantic task is equivalent.
* [ ] Correct native templates are used.
* [ ] Generation settings are compatible.
* [ ] Batch/padding behavior is compatible.
* [ ] Same parser/scorer is used.
* [ ] Same task/reasoning mode is used.
* [ ] Output-length differences are inspected if preference evaluation is used.
* [ ] Statistical uncertainty is considered when differences are small.

---

## 69. Before Selecting a Checkpoint

* [ ] Target capability was evaluated.
* [ ] Supporting capabilities were evaluated.
* [ ] Capability budget was checked.
* [ ] Qualitative outputs were inspected.
* [ ] Stopping/repetition was checked.
* [ ] Parser/format improvements were separated from semantic gains.
* [ ] Relevant regressions were measured.
* [ ] Exact checkpoint/artifact is recorded.
* [ ] Selection rationale is documented.

---

## 70. Before Declaring Success

* [ ] Target improvement is demonstrated.
* [ ] Improvement is practically meaningful.
* [ ] Supporting capabilities remain within budget.
* [ ] General regressions are understood.
* [ ] No known contamination invalidates the result.
* [ ] Evaluation matches the intended baseline protocol.
* [ ] Parser overfitting was considered.
* [ ] Response-length bias was considered where relevant.
* [ ] Judge-origin bias was considered where relevant.
* [ ] Manual inspection does not contradict automatic metrics.
* [ ] Suspicious results were investigated.
* [ ] Merged/quantized/deployment artifact was evaluated if different.
* [ ] Long-context regression was tested if long context matters.

---

# Part XI — Agent Rules

```text
IF evaluating a fine-tuned model:
→ load the frozen evaluation protocol
→ do not invent more favorable settings
```

```text
IF comparing an instruct starting model:
→ preserve prompt/generation parity where possible
```

```text
IF comparing a raw foundation model with an instruction-tuned result:
→ use appropriate prompting for each
→ preserve semantic task equivalence
→ document protocol differences
```

```text
IF exact-match scoring requires answer extraction:
→ inspect parser success separately from semantic correctness
→ do not mistake parser compliance for capability
```

```text
IF a benchmark score changes dramatically:
→ check contamination
→ check parser/scoring
→ check prompt/config parity
→ then interpret model change
```

```text
IF preference/judge results improve while responses become much longer:
→ inspect verbosity bias
→ report response-length statistics
```

```text
IF the judge is closely related to the synthetic-data teacher:
→ flag possible origin bias
→ seek independent validation for important conclusions
```

```text
IF evaluating a merged or quantized model:
→ evaluate that exact artifact
→ do not reuse adapter-mode scores as production evidence
```

```text
IF merged performance is worse than adapter-mode performance:
→ check base revision
→ check adapter scaling
→ check merge implementation
→ check dtype/precision
```

```text
IF long-context behavior matters:
→ test it explicitly
→ test the deployment serving configuration as well
```

```text
IF two evaluation protocols differ materially:
→ do not report the scores as directly comparable
```

```text
IF the test set repeatedly influences experiment decisions:
→ stop treating it as a clean final test
→ introduce a fresh holdout
```

---

# Final Principle

Evaluation should answer:

```text
Did the model learn what we wanted?

Was the gain semantic or merely formatting?

How large is the gain?

What capabilities were lost?

Are those losses acceptable?

Could the measurement itself be misleading?

Does the improvement survive independent checks?

Does the actual deployment artifact preserve it?
```

The purpose of evaluation is not to prove that the fine-tuned model is better.

It is to determine, as objectively as possible, **what changed and whether that change is useful**.
