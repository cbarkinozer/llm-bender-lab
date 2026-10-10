# Owner clarification and environment check — 2026-10-05

## Objective refinement

The owner wants human/LLM collaboration on unit-test quality, with personal
review of every evaluation output in Argilla. Passing pytest is a correctness
gate, not sufficient evidence of useful tests. Assertion strength and the
owner's existing test-smell rubric are central. Mutation detection remains
supporting behavioral evidence; the earlier proposed mutation-primary metric
is superseded pending a frozen quality rubric. No reward weights are selected.

Locate the owner's existing rubric before inventing a replacement. It was not
found in the unit-test-generation directory during this inspection.

## Observed local environment

- Apple Mac mini M4, 24 GB unified memory.
- macOS 26.5.1, build 25F80.
- Node v26.3.1.
- Installed Pi: 0.80.1, @earendil-works/pi-coding-agent.
- npm registry latest checked today: 1.0.3; Node requirement >=22.19.0.
- Registry integrity for 1.0.3:
  `sha512-t2lb0dw4y/jr5a2PRo6eTHGTZOPB3/YAMVyhhYFC1W3Hl5xE+462I/gMWjF4gCLuhGipNEfuNqONFmdqLFz4SQ==`.
- No Pi update performed; latest observed version is not the installed version.
- No llama-server or mlx_lm executable found on PATH. This is not a complete
  filesystem/package inventory.

Backend and precision are reopened for discussion: FP16 (assuming the owner's
"fp1" means FP16), MLX or llama.cpp Q4. Memory and end-to-end Pi tool/template
behavior must be measured before freezing a choice. No downloads or installs
performed. Precision and runtime are separate choices.

## Proposed evaluation sequence, not frozen

Use 10 tasks to debug execution and review; 20 separate development tasks to
calibrate the rubric; then roughly 100 grouped holdout tasks if review effort
allows. Pilot/development items must not be relabeled as untouched final test.
Review paired thinking-off/on outputs blind to model condition where possible.
Store original output, code, grader evidence, judge suggestions and human
decisions separately. Human edits are not the original model's score.

Prefer suitable deterministic Python test-generation tasks over leaderboard
prestige. SWT-Bench is directly relevant to reproduction-test generation;
LiveCodeBench needs adaptation from competitive programming. Adapted tasks form
a new benchmark and cannot inherit original leaderboard comparability.
Audit source licenses, actual item/code dates and near-duplicate families.
New benchmark publication dates alone do not establish uncontaminated tasks.
The Qwen3.5-4B card inspected today did not specify a training-data cutoff.

## Training remains undecided

SFT is not mandatory before GRPO. Direct RL needs useful baseline trajectories
and reward variation. GRPO is an optimizer; RLVR describes verifiable reward.
A human-calibrated judge plus execution/mutation signals is a hybrid reward,
not a pass-only RLVR objective. Human preference pairs may also support DPO.
Training rewards, rubric calibration and evaluation feedback must remain
separate from the final held-out tasks. No training or GPU rental authorized
by this design discussion.

## Research references

## Follow-up owner decision and supplied research

Owner selected llama.cpp with 4-bit GGUF for broader deployment; MLX and
full-precision deployment are no longer primary candidates. Exact GGUF variant
and artifact remain pending. GGUF is a deployment format, not QLoRA training;
training/export compatibility still needs a separate check.

Sources supplied locally:
- `/Users/cbarkinozer/Downloads/tests-that-run-but-do-not-test-paper.tex`
- `/Users/cbarkinozer/Downloads/Evaluating Small Language Models for AI-Driven Python Unit Test Generation.md`

Use the newer paper's oracle taxonomy: TRIVIAL (statically satisfied,
SUT-independent), WEAK (coarse SUT-derived property), STRONG (specific value,
content, exception/warning, state or interaction contract), UNKNOWN (unresolved
semantics/provenance). Require runtime reachability for the non-trivial gate.
Strong specificity does not establish semantic correctness. The paper reports
limitations in strong-only classification and human judge validation; do not
carry historical validation claims forward to this new experiment.

The quality rubric covers robustness, assertion strength, readability and
conciseness. The early thesis describes Assertion Roulette, Eager Test, Mystery
Guest, Magic Number Test, Obscure Test, Lack of Cohesion, Conditional Test Logic,
External Dependency, Unverified Action, Trivial Assertion and Duplicated Setup.
Treat structural smell detectors as review suggestions rather than automatic
penalties: the thesis itself discusses false positives, including missing
assertion messages under modern pytest and safely isolated external resources.
The newer taxonomy distinguishes weak nullity checks from trivial assertions;
do not merge the older smell definition into the newer oracle classification.

Owner prefers externally trusted benchmark evidence and fresh tasks over only
an in-house benchmark. September 2026 Multi-SWT-Bench converts older
Multi-SWE-Bench source instances; publication recency does not establish task
recency. SWE-rebench is a candidate source of recent dated Python repair tasks,
but a test-generation conversion would be a separately labeled adaptation,
not an official original benchmark score. No benchmark is selected yet.

Additional references:
- https://arxiv.org/html/2609.34752v1
- https://huggingface.co/datasets/nebius/SWE-rebench

- Pi: https://github.com/earendil-works/pi
- Qwen card: https://huggingface.co/Qwen/Qwen3.5-4B
- MLX LM: https://github.com/ml-explore/mlx-lm
- llama.cpp: https://github.com/ggml-org/llama.cpp
- SWT-Bench: https://github.com/logic-star-ai/swt-bench
- LiveCodeBench: https://github.com/LiveCodeBench/LiveCodeBench
- GRPO: https://huggingface.co/docs/trl/grpo_trainer
- DPO: https://huggingface.co/docs/trl/dpo_trainer
