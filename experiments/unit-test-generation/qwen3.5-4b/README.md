Current dataset profile: [token distributions, complexity, domains and semantic-overlap review](exp-002-task-test-sft/DATASET-PROFILE.md). Three cross-split taught-principle overlaps require an explicit evaluation interpretation; counts/splits are unchanged.

Current label audit: [78-candidate native masking checks passed](exp-002-task-test-sft/NATIVE-LABEL-AUDIT.md). Actual trainer batch parity remains unverified. Semantic near-duplicate review and baseline runtime/protocol are next; training remains disabled.

Current independent-review fixes: [REVIEW-FIXES.md](exp-002-task-test-sft/REVIEW-FIXES.md). All 15 v04 plans serialize shared-file edits; active-data checks pass. Label audit and baseline remain pending.

Current intent-only policy and reviewed planning/decision revisions: [CONTENT-REVIEW.md](exp-002-task-test-sft/CONTENT-REVIEW.md). Repository implementation source is audit-only and excluded from model input/targets. Counts remain 95 total / 78 train-family candidates; no training has started.

Current reliability work: [audit, corrected preflight row, 22 separate decision drafts and prepared baseline packet](exp-002-task-test-sft/RELIABILITY-PREPARATION.md). Test count remains 58; inference and training remain pending.

Current data additions: [58 task-test candidates and 15 separate planner drafts](exp-002-task-test-sft/CURRENT-CANDIDATES.md). The test candidates split 50/5/3; planning is not enabled for training.

> Existing-source expansion, 2026-10-31: [exp-002 pilot-v02](exp-002-task-test-sft/EXPANSION-RESULTS.md) builds 38 task candidates across all seven training families. A 62-proposal backlog is grounded in pinned source files; it is not yet training data. The two evaluation families remain excluded. Earlier eight-row pilot counts below are historical.

> Active direction, 2026-10-31: [task-to-tests SFT](exp-002-task-test-sft/README.md) supersedes the whole-app training plan. The initial pilot contains eight task candidates and two separate planning contexts from existing training families. Planning/code generation stay outside the first SFT objective; expansion toward 100 tasks comes before a fresh baseline. Whole-app v07 remains preserved.

> Current, 2026-10-31: [revision 07](exp-001-local-thinking-10/app-core-v07/README.md) addresses the imported static AI review. Fresh checks: 153 passing cases, 81 detected faults, three passing order seeds; maximum full sequence 7,548 tokens. The owner selected AI review for this demo; revised packets await that review. No whole-app baseline or Qwen SFT has run. Earlier status blocks below are history.

> Current, 2026-10-31: [revision 06](exp-001-local-thinking-10/app-core-v06/README.md) corrects the codelang-detect
> fixtures and API decisions; the other eight model conversations match v05.
> Review: http://127.0.0.1:7900/dataset/b3adc9b0-a181-4c1f-9c51-d7e4512b677e/annotation-mode
> A one-example TXT now includes full per-requirement fault evidence and blank annotations.
> Previous views remain intact. No model baseline or SFT has run.

> Current review, 2026-10-31: [revision 05](exp-001-local-thinking-10/app-core-v05/README.md).
> Code display is HTML-escaped, the new meta-text defect category is available,
> and numbering/process-text/preservation pre-checks pass. Review:
> http://127.0.0.1:7900/dataset/ae9c43c9-54ea-4602-9d4d-56741869b59a/annotation-mode
> Previous datasets and annotations remain preserved; no SFT has started.

> Current format revision, 2026-10-31: [app-core-v04](exp-001-local-thinking-10/app-core-v04/README.md).
> Natural requests and shared system instructions are separated from construction/review metadata.
> Tests and application behavior match v03; record-specific executor work is archived separately.
> Review: http://127.0.0.1:7900/dataset/7500c36b-0971-41bd-91c5-765d6e7add5e/annotation-mode
> Earlier status blocks below are history. No whole-app SFT has run.

> Current scope, 2026-10-30: **nine whole-app framing-B candidates**, not the
> historical ten function-contract pilot. See [revision 03](exp-001-local-thinking-10/app-core-v03/README.md).
> 142 reference cases pass, 57 targeted faults cover 53 core requirements,
> three test orders pass and every full sequence fits 8K. Owner review is pending:
> http://127.0.0.1:7900/dataset/f7c79cb7-8943-4281-98d1-4e9128a2b529/annotation-mode
> No whole-app baseline or SFT has run. Earlier plans below are historical.

> Active scope update, 2026-10-29: paper continuation paused. Complete the
> [quick ten-example thinking-SFT demo](exp-001-local-thinking-10/README.md),
> then reuse the task setup for GRPO. Historical research plans below are deferred.

# Python unit-test generation — Qwen3.5-4B

Current owner priority, 2026-10-29: [paper continuation initialization](CONTINUATION-20261029.md)
and the [10-task local requirements-to-tests pilot](exp-001-local-thinking-10/README.md).
Requirements/API in, pytest tests out; untouched Qwen3.5-4B with thinking enabled
on the Mac. Establish test quality first, then study thinking SFT, then separately
measure downstream code generation against frozen tests. Occam2 is deferred.
The ten contracts remain drafts awaiting reference/fault preflight; no new
10-task inference or training result exists. This decision supersedes historical
thinking off/on and RL-first priority statements below.

Current pilot: [Stage A v01](exp-000-baseline/requirements-pilot/STAGE-A-V01.md).
Generation settings are frozen; one new task is ready for owner quality review.
TOML reference-based scoring is quarantined following confirmed contract failure.

## Current direction — requirements-first TDD (2026-10-17)

Follow the [requirements-first protocol](REQUIREMENTS-FIRST-PROTOCOL.md): compare
untouched direct-code and prompted test-first generation, review/freeze tests
before implementation, then study separate SFT and SFT+GRPO improvements. Test
quality uses the owner's prior taxonomy; final code correctness uses independent
hidden evaluation. Stage B permits production edits with frozen tests read-only.
This supersedes the earlier test-only scope and conditional GRPO-first plan below.
A pinned DeepSWE download and descriptive EDA are complete. A 20-task development
shortlist is prepared; contracts/interfaces and runnable task environments remain
to be validated. Generation smokes are not benchmark scores.

## Status and owner decision (2026-10-05)

Owner refinement, 2026-10-17: start with **20 fresh, externally sourced development
tasks**, evaluate with the prior quality/smell taxonomy, then study GRPO and
independent broader-SWE transfer. The current [research plan](RESEARCH-PLAN-20261017.md)
takes precedence over earlier open task-mode and pilot-size decisions.

**Planned; environment setup is underway. No benchmark or training has run.** The next phase
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

The owner-selected primary objective is human-reviewed test quality: robustness,
assertion strength, readability and conciseness, using the supplied paper rubric.
Personal Argilla review covers every evaluation output. Execution success and
runtime-reached non-trivial oracles are gates/diagnostics; mutation or real-bug
detection is supporting behavioral evidence. Passing pytest alone is insufficient.
See [design notes](DESIGN-NOTES-20261005.md) and [TODO](TODO.md).

Freeze quality aggregation, correctness handling and detection denominators on
train/development data before final evaluation. Treat static smell detections as
review suggestions; a strong-looking assertion may still be semantically wrong.
Preserve invalid and failed suites in all-task reporting.

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
