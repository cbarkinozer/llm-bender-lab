# Research plan — owner direction, 2026-10-17

Latest accepted refinement: [requirements-first protocol](REQUIREMENTS-FIRST-PROTOCOL.md).
Primary workflow is requirement → validated/frozen tests → implementation,
with separate test-quality and independent implementation evaluation. Compare
direct-code and prompted-TDD baselines, then separate SFT and SFT+GRPO experiments.
This supersedes earlier correct-code-only pilot scope and GRPO-first method order.

## Research questions

1. How well does untouched Qwen3.5-4B Q4_K_M generate useful Python unit tests
   through Pi/llama.cpp on the Mac mini M4/24 GB?
2. Can GRPO improve test quality on unseen tasks under the same deployment protocol?
3. Does that training also improve broader software engineering performance on
   an independent benchmark such as Datacurve DeepSWE?

## Start with 20 development tasks

Keep collection bounded at 20 accepted tasks before expanding data work. Begin
with English requirements and approved existing public interfaces, generating
tests before feature implementation. Tests are validated and frozen before the
implementation stage. Issue-reproduction testing remains a separate condition.
Historical paper fixtures remain infrastructure diagnostics, not fresh evidence.

Prefer trustworthy external sources. Freeze task IDs before generation, selected
by validity, freshness, behavior diversity and runtime compatibility rather than
model success. Record rejected candidates and reasons. These 20 tasks are a
development pilot: once their outputs inform decisions, they cannot serve as an
independent final test or establish broad generalization.

Each input needs an instruction, original source/interface, explicit behavioral
contract, approved context/dependencies, writable test path and allowed command.
Independently validate reference behavior; reject ambiguous contracts. Keep gold
tests, solutions, private mutants and grader metadata out of model context.
Inspect issue/PR text for solution leakage when adapting external tasks.

Owner clarification: accept the dataset release after the stated Qwen3.5-4B date
(2026-03-09) as sufficient freshness evidence. DeepSWE's Hub repository was created
2026-06-01, 84 days later. Underlying code exposure remains acknowledged; exhaustive
historical exposure checks are not required or a blocker. Keep ordinary provenance,
source hashes, licenses and train/evaluation separation. The model date is owner-
supplied and is not a verified training cutoff. See the
[download/card audit](exp-000-baseline/benchmark-audit/deep-swe-20261017/README.md).

### External sources checked on 2026-10-17

- [Datacurve DeepSWE](https://deepswe.datacurve.ai/) and its
  [paper](https://arxiv.org/abs/2607.07946): original long-horizon engineering
  tasks with behavioral verifiers; candidate for broader-SWE transfer. Authors'
  contamination claims are not an independent audit of this model. Check artifact
  access, licenses, Python availability, difficulty and ARM64/runtime feasibility.
- [SWT-Bench](https://github.com/logic-star-ai/swt-bench): relevant test generation
  for issue reproduction, but older tasks do not establish freshness. ARM64
  support is documented as experimental; its task mode differs from this pilot.
- [SWE-rebench](https://github.com/SWE-rebench/SWE-bench-fork): dated repair-task
  source candidate. Conversion to ordinary test generation is our adaptation,
  not an official benchmark score. See the existing baseline benchmark audit.
- [Qwen3.5-4B model card](https://huggingface.co/Qwen/Qwen3.5-4B).

DeepSWE is downloaded and pinned. A 20-repository provisional shortlist is in
`exp-000-baseline/requirements-pilot/candidate-manifest.json`; it still needs
task-level interface and execution preflight. No final holdout is frozen.

## Untouched-model baseline and human review

Use the already identified untouched Q4_K_M artifact, preserving its hash and
effective Pi/server/template configuration. Finish protected per-task execution,
then run an infrastructure smoke before the full pilot. Compare thinking off/on
with matched total token/time allowances. Preserve original suites, tool traces,
repairs, termination, tokens, latency and memory. An episode with repairs is not
single-shot Pass@1. Do not silently repair scored model outputs.

Use the owner's paper/thesis taxonomy and `quality-rubric-v0.1.md`. Review in
Argilla blind to model identity and automated suggestions, retaining a separate
evidence-assisted adjudication. Report independently:

- Execution health: syntax, imports, collection, nonempty tests, pass/fail against
  verified correct code, timeout, infrastructure failures and repeat-run stability.
  Enforce unchanged source hashes and independently execute generated suites.
- Importance/usefulness: which contract behaviors, boundaries, errors and
  regression risks each test protects, with concrete evidence. Do not invent a
  scalar importance score or equate usefulness with assertion count.
- Reached TRIVIAL/WEAK/STRONG/UNKNOWN oracle sites, SUT dependence and semantic
  correctness. Specific assertions are not automatically correct assertions.
- Robustness, assertion strength, readability and conciseness using the existing
  rubric; contextual smell evidence, severity and impact using the thesis categories.
- Supporting coverage/target exercise and valid bug/mutant detection evidence.

Passing pytest alone is insufficient. Preserve failed suites in all-task reports.
Calibrate aggregation on development data before freezing final evaluation.

## GRPO learning and improvement

Explain one actual episode before selecting a stack. GRPO samples several
attempts at a task, scores them, and updates the policy using their relative
rewards. Reward quality determines what it learns; pytest-only rewards can favor
empty or uninformative tests.

Use separate training/development task groups and validate rewards against the
owner's judgments and deliberately weak/adversarial suites. Verify useful reward
variation, action masks and rollout/update linkage before a tiny LoRA pilot.
GRPO is the intended method; any SFT warm-up needs evidence of a specific
format/tool deficit and a separate documented experiment.

Expected path: compatible original weights on rented NVIDIA hardware, validated
export to Q4_K_M, then fresh Mac/Pi evaluation. Frozen local GGUF traces are not
automatically on-policy GRPO data. No GPU rental, framework, reward weights or
hyperparameters are selected now.

## Independent evaluation and broader-SWE transfer

Before training, freeze separate unit-test holdout groups and broader-SWE tasks
and measure untouched-model baselines. Keep their feedback out of reward design,
training and checkpoint selection. Use development evidence for those decisions.

After selecting the candidate, compare actual Q4 deployments with matched prompts,
tools, thinking and budgets within each task family. Broader SWE permits source
edits in a separate sandbox. Pi runs are a labeled harness adaptation if the
benchmark uses another reference harness; subsets are not full benchmark scores.

Report paired outcomes, failure types, resources and uncertainty. Better unit
tests without broader-SWE improvement is a valid negative transfer result.
Broader improvement is evidence under the measured protocol, not proof of all
general code-generation gains. Consider a matched training-compute control when
feasible to distinguish specialization from extra training.

## Immediate next action and status

Audit accessible external candidates for the 20 inputs and finish protected Pi
execution. Produce accepted/rejected task manifests, run the untouched baseline
and review original suites before expanding data work or starting GRPO.
Two development generation diagnostics now exist; see
`exp-000-baseline/requirements-pilot/README.md`. No training or scored benchmark
evaluation has run.
