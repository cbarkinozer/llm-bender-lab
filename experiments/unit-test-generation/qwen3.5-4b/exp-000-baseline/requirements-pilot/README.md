# Requirements-first development pilot

## Status and first observations — 2026-10-17

Prepared 20 candidate tasks from 20 repositories. They are not yet a validated
20-task benchmark. Two diagnostic generations on one TOML conversion task ran
through untouched Qwen3.5-4B Q4_K_M and Pi. Both originals are preserved and rejected
at Stage A; no model implementation has been generated and no training has run.

| Diagnostic | Time | Pi input/output tokens | Test functions | Independent reference outcome |
|---|---:|---:|---:|---|
| Requirement only | 69.169 s | 736 / 2,000 | 15 | Collection error: unsupported top-level import |
| Requirement + verified existing API context | 90.737 s | 975 / 2,615 | 19 | Collection succeeded; all 19 failed on invented fixture methods |

Both emitted one complete Python block, parsed successfully and stopped normally.
Syntax and test counts did not establish useful tests. The second diagnostic uses
different input context, so this is not a frozen paired benchmark comparison.
No failure trace or reference patch was provided to either generation.

## Environment and evidence

- Pi 1.0.3, llama.cpp 0.5.0/build 11146/commit `7fe450e19`, Darwin ARM64.
- Existing Q4_K_M file was SHA256-checked by `start-server.sh` before startup.
- Thinking off, output cap 3,072 tokens, host generation timeout 240 seconds,
  temperature 0.6, top_p 0.95, top_k 20, seed 42, context 8,192.
- All Pi tools, extensions, skills, context-file discovery and session saving
  disabled. Generation saw requirement/repository metadata and, in diagnostic 2,
  verified existing API descriptions. No implementation or hidden tests were supplied.
- Pinned TOMLKit base `dd05eebc8ed9e30fc6c223088a5a450cb54c1cab` cloned outside Git.
  Reference patch applied cleanly. Its SHA256 and execution command are recorded.
- Small trusted reference sanity checks passed: imports, document identity,
  table conversion, value preservation, roundtrip and missing-key exception.
  This is not full semantic validation of the benchmark reference.
- Generated-suite execution used a pinned local Docker image ID, non-root user,
  read-only source/tests/root filesystem, no network, 1 CPU, 512 MB memory,
  process limit and bounded timeout. Source and original test hashes were preserved.
- Existing isolation probe passed. The new preflight runner was independently
  checked with known passing, wrong-expectation and import-error suites, preserving
  hashes and returning expected pytest exit codes 0, 1 and 2.

Raw Pi event streams, effective configuration, generated tests and execution logs
are outside Git under `~/.cache/llm-bender-lab/requirements-pilot-v01/`.
Small summaries, provenance and static review findings are recorded here. Tokens
are Pi-reported; memory/throughput were not independently instrumented for these runs.

## Requirement alignment findings

The first suite misuses existing APIs and contradicts required return semantics.
It treats an ordinary nested table as an array-of-tables failure case and uses a
data key named `comment` as evidence of comment migration. The second correctly
imports existing classes but invents document construction methods. It also expects
errors for explicitly permitted inline-table inputs, includes unused fixtures,
and has an unused roundtrip helper with only a weak non-null assertion.

These are assistant development reviews, not the owner's human ratings. No
numeric quality or smell score is assigned. No conversion target was reached
in the runtime failures; static-looking assertions receive no runtime credit.
Original suites were not repaired or used to train the model.

The finding supports evaluating requirement alignment, executable health and
implementation correctness independently. One task does not establish that SFT
is necessary or that these failures characterize the whole model.

## Reproduce and next work

From repository root:

```sh
.venv/bin/python scripts/evaluation/prepare_requirement_pilot.py
bash experiments/unit-test-generation/qwen3.5-4b/exp-000-baseline/start-server.sh
# Run in a second terminal; every generation creates a fresh preserved run directory.
.venv/bin/python scripts/evaluation/run_requirement_smoke.py
.venv/bin/python scripts/evaluation/run_requirement_smoke.py --with-approved-context
```

The approved-context variant currently exists only for the TOML task; its text is
outside Git with source/context hashes in `tomlkit-context-provenance.json`.
Use `preflight_requirement_suite.py --help` to run preserved suites against a
prepared reference; it does not build references, repair tests or assign rewards.

Next provide adequate public interface/context and complete requirement mapping
for the first task, then review original tests against the owner's taxonomy.
Implement frozen-test Stage B and independent hidden grading before expanding
to 20 paired episodes. Keep the shortlist's repository groups out of the final
broader-SWE transfer holdout and never train on DeepSWE task content.


## Continuation: fixture context, reference validation and budget correction

Two fresh thinking-off generations with verified fixture examples were preserved:

| Public context variant | Collected cases | Result |
|---|---:|---|
| API + parsing fixtures v02 | 25 | 12 passed, 13 failed |
| API + contract clarifications v03 | 22 | 17 failed, 5 fixture errors |

Both were rejected. The implementation stage was not started from these suites.
The tests-first runner's rejection gate was checked without issuing a model call.
Static review covers invented APIs, unsupported error-message expectations,
invalid negative fixtures, conditional test logic and missing fixture dependencies.

The complete reference environment is now validated: 60 hidden feature tests and
964 original regression tests pass. Missing pinned submodule fixtures were restored;
file-writing regression fixtures run from a temporary container copy while source
remains read-only. `tomlkit-grading-harness-validation.json` validates the reusable
independent grader against the reference, not a generated-code candidate.

A direct-code diagnostic repeated helpers and stopped with `length`, producing
no complete implementation. Inspection of installed Pi 1.0.3 found a fixed 4,096
context-token reserve, reducing output room in an 8,192-token model context.
Configured output limits were ceilings, not guaranteed transmitted allowances.
The exact old request payload was not captured. See `pi-context-budget-audit.json`.

The task-owned server was restarted with `BENDER_CONTEXT_TOKENS=16384`. Both
runners now obtain the actual server context from `/props` and set Pi's model
context to match. A larger-budget thinking diagnostic is separate from previous
conditions. Do not pool these development variants into a benchmark score.

One direct-code attempt was stopped before scoring to correct an assistant's
API-context transcription error (`DottedKey.keys` versus existing key iteration).
It is preserved as infrastructure-invalid and excluded from model conclusions.
No reference or hidden test bodies have been sent to any generation.


## Latest completed diagnostics with corrected 16,384-token context

- Thinking-enabled requirement-to-tests generation: 20 cases collected, **16
  passed and 4 failed** against the reference. Original suite rejected, unchanged.
  Two failures are clear assertion/contract errors, another relies on unsupported
  internal lookup shape, and one exposes a separately reproduced suspected
  reference defect on valid mixed dotted/nested TOML. Do not label every failure
  a model mistake or treat the reference's supplied tests as exhaustive proof.
- Actual reasoning content is preserved (2,611 characters), despite Pi reporting
  zero reasoning tokens. Separate reasoning-token accounting remains unverified.
- Direct-code generation, thinking off: complete three-file model output applied
  only in a new external worktree. **4/60 hidden feature tests passed; 964/964
  regression tests passed.** No repairs or hidden feedback were given to Pi.
  Source hashes were unchanged during grading. Example faults include missing
  imports, returning items instead of the document and the wrong exception base.
- No test-first implementation was run: there is no accepted frozen original
  suite. This remains a Stage A failure, not a repaired model success.

`tomlkit-development-outcome.json` records the result. These diagnostic conditions
vary in prompts, context, budgets and thinking, so no causal TDD gain or aggregate
benchmark score is reported. Stop prompt-tuning this task after these observations.
Adjudicate the reference anomaly and freeze the task context and bounded episode
protocol before scaling the initial 20-task development pilot. No training ran.
