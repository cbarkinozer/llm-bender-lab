# slm_test_generation — assistant review

## Whole-app request

Build me a Python research pipeline for benchmarking small language models that generate tests from functions. I want to give it task records, model outputs and run configuration, execute each generated pytest suite in an isolated network-disabled environment with a time limit, and get reproducible per-task results and comparison tables. Keep raw generations unchanged and distinguish collection errors, runtime failures, timeouts and genuinely passing suites. A suite that passes without exercising a meaningful assertion must not be reported as a useful test-generation success. Record which oracle checks actually execute and distinguish trivial, weak, strong and unresolved checks using an explicit taxonomy, while keeping semantic correctness as a separate judgment. Support context/dependency metadata, aggregate with the correct eligible-task denominators, retain unsuccessful and missing observations visibly, and report mutation results with clear unconditional and conditional denominators. Save task identities, configuration and source revisions so I can trace every reported number. Keep the pipeline small and usable with documented commands and fixture-based tests, and never launch model inference or alter the frozen benchmark merely to run its own tests.

## Decisions and corrections

- Use fresh synthetic utility fixtures, never frozen paper benchmark tasks/predictions.
- A strong but incorrect oracle must remain a failed test; reachability and strength are independent.
- Infrastructure errors and missing observations must stay disclosed; choose denominators explicitly before adding aggregation tests.

## Important limits / missing acceptance checks

- Current core suite verifies oracle taxonomy/reachability, not isolated execution, aggregation, mutation denominators or manifests.
- The app request is a pipeline MVP; the full paper reproduction is outside it.

## Requirement-to-test review

### R1 — Keep raw generations and distinct execution outcomes.

**Core check:** Fixtures for syntax error, failing assertion, timeout and pass retain their original text and yield distinct result codes.

**Current coverage:** gap. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R2 — Require a runtime-reached meaningful oracle for non-trivial success.

**Core check:** assert True alone, an assertion in an uncalled function, and a skipped assert do not pass the meaningful-oracle gate; a reached exact result assertion does.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R3 — Keep oracle strength separate from correctness.

**Core check:** A concrete but wrong equality is specific/strong while execution fails; a result-is-not-None check is weak, not automatically strong.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R4 — Use correct aggregation denominators and preserve missingness.

**Core check:** For four eligible tasks with two execution passes, one meaningful pass and one missing result, report 2/4 and 1/4 with the missing task disclosed, not 2/3.

**Current coverage:** gap. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R5 — Keep mutation denominators explicit.

**Core check:** For four eligible tasks, two valid suites and one detected fault among one fault per task, unconditional score is 1/4; conditional score is 1/2.

**Current coverage:** gap. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R6 — Preserve reproducibility and sandbox restrictions.

**Core check:** Manifest round-trip preserves task IDs/config/hash; sandbox command enforces no network/read-only mounts/timeouts; no training/evaluation files overwritten.

**Current coverage:** gap. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

## Core tests included

- `tests/test_core.py::test_oracle_strength_is_explicit`
- `tests/test_core.py::test_uncalled_assertion_is_not_runtime_evidence`
- `tests/test_core.py::test_reached_strong_oracle_satisfies_gate`
- `tests/test_core.py::test_trivial_pass_is_not_meaningful_success`
- `tests/test_core.py::test_wrong_exact_assertion_is_strong_but_not_success`

## Manual checks

- Reproduce a small report from saved raw records and inspect table labels.
- Sandbox guarantees need an actual isolation probe; command-string assertions alone are insufficient.
