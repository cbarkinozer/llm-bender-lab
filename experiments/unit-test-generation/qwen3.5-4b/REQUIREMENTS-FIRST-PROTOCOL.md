# Requirements-first pilot protocol — development draft, 2026-10-17

## Accepted research question

Does training a small model to generate requirement-faithful, useful tests before
implementation improve independently measured code correctness beyond prompting
alone? Test-first generation is established research; the contribution under study
is measured quality and downstream benefit on the actual 4B Q4/Pi deployment.

This supersedes the earlier correct-code-only pilot as the primary workflow.
Preserve that mode as a separate optional test-generation comparison. Freshness
criterion remains the owner's accepted dataset-after-model release comparison.

## Four conditions, introduced in order

| Condition | Weights | Process |
|---|---|---|
| Direct-code baseline | Untouched Qwen3.5-4B | Requirement → implementation |
| Prompted TDD baseline | Same untouched model | Requirement → tests → review/freeze → implementation |
| SFT TDD | Separately validated training demonstrations | Same staged TDD process |
| SFT + GRPO | Selected SFT parent and separate training tasks | Same staged TDD process |

Compare direct-code versus prompted TDD before paying for training. SFT teaches
the sequence; the harness enforces stage permissions. GRPO remains a later,
separate experiment after validating rewards and stack compatibility. Training
data must be separate from DeepSWE evaluation tasks, variants and repository groups.

Match total inference token/time/repair allowances across conditions. Account for
all thinking, test generation and implementation tokens. Report human review time
and intervention separately; a human-assisted TDD run is not autonomous model
performance. Use the same interface clarifications across paired conditions.

## Task input and development shortlist

`exp-000-baseline/requirements-pilot/candidate-manifest.json` lists 20 tasks from
20 repositories, selected before observing model success. Selection is purposive,
not random or a claim of representative difficulty. Unselected Python tasks and
reasons are recorded. Packet text is in the external cache; raw benchmark content
is not copied into Git. Each packet preserves the verbatim requirement hash.

The shortlist is provisional until contract/interface and environment preflight.
Do not silently simplify full requirements or replace difficult tasks based on
results. Narrowing a requirement creates a separately identified adaptation.
The initial no-source smoke measures requirement-only test emission, not complete
repository-agent performance. Record interface hallucinations and underspecification.

For actual runs, provide the English requirement and approved existing public
API context (imports, signatures, fixtures, dependency versions). Tests may inspect
the pre-feature repository but cannot see a new implementation, reference patch,
hidden verifier or hidden tests. Record approved context hashes. Prompt wording
that asks to implement describes intended behavior; the wrapper requests tests only.

## Stage A: requirements to tests

1. Extract testable behaviors and interface ambiguities from the requirement.
2. Generate tests without writing the feature implementation. Preserve original
   tests, raw Pi events, effective prompts/config and output/termination statistics.
3. Check syntax, importability, collection, real target-related assertions and
   assertion semantics separately. New-feature tests can legitimately fail on
   the original implementation. Import failure is not evidence of bug detection.
4. Review each expected result against the requirement. Record behavior covered,
   importance/risk, oracle class, semantic correctness and contextual test smells.
   Use the owner's prior rubric; do not reward arbitrary assertion/smell counts.
5. Independently check correct-reference passing and meaningful bad-variant
   detection when available. Reviewer execution is not visible feedback to Stage A.
   A reference solution is evidence to validate, not unquestioned ground truth.
6. Freeze original test bytes and SHA256 after review. Mark accepted, rejected,
   ambiguous or infrastructure-blocked. Retain all-task denominators. Rejected
   original suites remain failures; human-repaired suites form a separate condition.

Passing generated tests on generated code does not validate the requirement.
Both can share the same misunderstanding. Human contract review and independent
hidden evaluation address different parts of that problem.

## Stage B: frozen tests to implementation

The implementation stage receives the same requirement/context plus accepted
frozen tests. Implementation files become writable in a separate workspace;
frozen tests remain read-only. Run bounded commands inside the task container.
Never expose the Docker socket, home, credentials, verifier or hidden tests.
Do not permit implementation-side edits to weaken tests. Capture source diffs,
test hashes, repairs, execution and final termination independently.

Generated-suite passing is a diagnostic. Independently run original benchmark
hidden tests and regression tests on the submitted implementation. Do not show
hidden failures during the episode. Report requirement-to-test quality and
implementation correctness as separate outcomes, including their joint success.

## Gates and measured outcomes

- Workflow: tests created before implementation, frozen hashes preserved.
- Test health: syntax/import/collection/runtime status and meaningful assertions.
- Requirement alignment: correct expectations, missing important behaviors,
  unjustified restrictions, unsupported interfaces and ambiguity.
- Quality: the existing TRIVIAL/WEAK/STRONG/UNKNOWN taxonomy, robustness,
  assertion strength, readability, conciseness and contextual smells.
- Behavioral utility: correct-reference passing and held-back bad-variant detection.
- Downstream correctness: independent hidden functional tests and regression tests.
- Cost: total inference compute, tool/repair counts, latency and review effort.

Do not make the freeze gate disappear for unfavorable model outputs. Report
accepted-suite conditional results alongside full-pipeline all-task results.
Twenty development tasks calibrate this process; they do not establish population
performance. Exclude shortlisted repository groups from the later independent
transfer holdout, and freeze that holdout before training/checkpoint selection.

## Current execution boundary

The existing Docker isolation probe passes. It is a foundation, not a complete
repository sandbox. `run_requirement_smoke.py` uses Pi with all tools disabled,
no project context discovery and an ephemeral session. It captures generation
and parses syntax without executing generated code. `run_requirement_code.py`
requires accepted review, correct-reference passing and matching frozen hashes
before tests-first implementation. It can also run the independent direct-code
condition. Model output is constrained to three TOMLKit source-file operations
and applied only in a new external worktree. No test suite has yet passed that gate.

`grade_requirement_code.py` separately runs held-back tests and regressions in
bounded Docker, with no grading feedback sent to Pi. Reference calibration passes
60 feature and 964 regression tests. An independently reproduced reference anomaly
still needs contract adjudication. These scripts implement text-generation
episodes through Pi, not a full interactive repository-tool agent or a hardened
RL reward service. Original failures, context variants and truncations are preserved.

Pi 1.0.3 reserves 4,096 context tokens. The development server now uses 16,384;
generation scripts read the live context from `/props` to configure Pi. Configured
output ceilings and actual available output allowance are different quantities.

Next complete one task's contract/interface and reference environment, review
the generated suite, then enforce the frozen-test implementation stage before
expanding to 20 paired episodes. No SFT/GRPO training is authorized by a passing
generation smoke; required experiment preflight still applies.
