# Python unit-test generation — Qwen3.5-4B

## Status and owner decision (2026-10-05)

**Planned; no benchmark, baseline inference or training has run.** The next phase
is Python unit-test generation only. Occam/Turkish SFT is closed and deferred;
do not initialize this agent from the Occam response-style adapter by default.
The owner will continue on a Mac mini M4 with 24 GB unified memory, using Pi
and Q4 GGUF inference through llama.cpp. Finish the Turkish blog independently.

This narrows the original broad TDD/coding-agent roadmap: generate and improve
tests for fixed production code, not implement features or fix production bugs.
Task success is good executable tests, not a prose answer or a patch to production.

## Research question

Can verifiable-reward RL improve a 4B model's Python test generation, measured
on unseen task groups and on the actual local quantized deployment?

The immediate question is simpler: does the frozen 4B produce valid, useful tests
through Pi, and what does thinking add at a measured time/token cost?

## Scope and environment

- Use one task family, multiple tasks; no single-task memorization study.
- Initial candidates: deterministic Python functions/small modules with explicit
  contracts and a verified-correct implementation; pytest tests only.
- Agent may inspect source and approved docs, create/edit generated test files,
  and run an allowlisted test command. Production code is read-only.
- Separate the execution workspace from private grading data. No secrets, home
  mounts, network access or unbounded commands in the agent sandbox.
- Gate completion on successful test collection, non-empty real assertions,
  passing against the correct implementation, and preserved production hashes.
- Tests should detect held-back valid mutants/known-bad variants. Do not reward
  matching an existing buggy implementation or copying its mistakes as the spec.
- Tasks relying on nondeterministic networks, clocks or external services are
  excluded from the first pilot. Expand only in a separate documented experiment.
- English task specifications are fine; Turkish language/style is not a target.

## Baselines before RL

1. Untouched Qwen3.5-4B Q4, thinking off.
2. Same 4B artifact, thinking on; verify actual template and server behavior.
3. Optional Qwen3.5-9B Q4, thinking on, as a larger reference, not a teacher reward.

Keep task IDs, tool definitions, Pi prompt, timeouts and rollout allowances
fixed. Report actual tokens, latency, tool calls, termination and peak memory.
Use a fixed total token/time budget (thinking included) for the primary paired
comparison; additional larger-budget runs are separate, explicitly labeled.
Model-size or thinking improvements are not evidence of an RL gain.

Pin model/tokenizer revisions, GGUF file SHA256 and exact Q4 variant, converter,
llama.cpp build/commit, Pi version/commit and effective chat/tool template.
The Mac's 24 GB feasibility is an estimate, not a measured run. Load one model
at a time initially; start with bounded context and measure memory/throughput.

## Evaluation and reward design

Proposed primary metric: per-task mutation detection with a correctness gate.
For a fixed non-empty set of valid, behavior-changing mutants, score a test suite
only if it passes on the correct implementation; then report killed/evaluable
mutants. Empty, invalid or failing test suites receive zero. Final denominator,
timeouts, task weighting and aggregation must be frozen before baseline.

Report validity/pass-on-correct separately so an apparent kill gain cannot hide
false positives. Exclude equivalent/invalid mutants by the frozen verifier rules;
record every exclusion and never silently remove failures after seeing outputs.
Coverage is supporting evidence, not the primary objective. Catching import errors
or hanging a mutant is not automatically a semantic bug detection: classify it.

Reward-hacking controls: no editing source/grader/tests outside the writable
test directory; no disabling assertions, skip/xfail tricks, monkeypatching the
target into passing, reading mutant identities, deleting tests, or grading
through agent-reported exit codes. Enforce permissions plus hash/diff checks;
instructions alone are not a security boundary. Re-run tests independently.

Split by repository/source/problem family and near-duplicate groups, not random
rows. Training reward mutants and held-out grading variants remain separate.
Choose tasks with clear rights/provenance. Do not use final evaluation tasks,
mutants or grading feedback as training seeds, rewards or teacher prompts.

## RL plan — not a ready training recipe

After the local frozen baseline and verifier checks, evaluate a compatible
GRPO/agentic-RL implementation. The 4B generates its own tool trajectories;
trusted execution supplies rewards. Ensure nonzero successes and a useful
spread of rewards before paying for a long training run. If all rollouts fail,
diagnose tooling/task difficulty before assuming more RL steps will help.

Start with native thinking enabled only if the baseline supports that decision.
Reward correct, useful tests, not lengthy thinking or self-reported reasoning.
Log final-answer/tool-action emission, thinking/output tokens, truncation,
repetition, unsuccessful episodes, KL/drift where applicable and reward components.
Tool results and environment/grader text must not become supervised model actions.
Verify action-token masks, old-policy log probabilities and rollout/update linkage.

9B demonstrations copied into 4B are distillation/SFT, not automatically RL.
The 9B may later generate verifier-approved demonstrations in a separate experiment;
do not use its subjective approval as the first pilot's main reward.
Frozen Q4 rollouts collected locally are not automatically on-policy GRPO data.

Expected main path: compatible original model + LoRA RL on rented NVIDIA hardware,
then validated merge/conversion to Q4 GGUF, then paired local deployment evaluation.
No GPU request or training now. Do not assume direct Q4 GGUF training in llama.cpp:
its training example is WIP/FP32-limited. MLX quantized LoRA on Apple silicon is an
optional separate learning exercise; Qwen3.5 training/export compatibility and
memory still need checking. MLX quantization is not interchangeable with GGUF.

## First deliverables on the Mac

See [TODO](TODO.md), [planned baseline](exp-000-baseline/README.md), and
[Mac handoff](../../../docs/MAC-MINI-HANDOFF.md). No dataset-size commitment,
hyperparameters, RL package pin or benchmark score is established yet.

## References checked 2026-10-05

- [Pi models/local connections](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/models.md)
- [Qwen3.5-9B thinking/tool interface](https://huggingface.co/Qwen/Qwen3.5-9B)
- [llama.cpp training limitations](https://github.com/ggml-org/llama.cpp/blob/master/examples/training/README.md)
- [MLX LM](https://github.com/ml-explore/mlx-lm)
- [TRL GRPO](https://huggingface.co/docs/trl/grpo_trainer)
- [Previously requested FineEnvs track](https://huggingface.co/spaces/FineEnvs/multi-harness-rl#introduction)

These are starting references, not evidence that Pi, this architecture, GRPO,
MLX export or the multi-harness implementation already work together.
