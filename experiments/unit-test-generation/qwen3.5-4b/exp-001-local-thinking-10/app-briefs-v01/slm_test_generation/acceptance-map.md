# slm_test_generation — draft core acceptance map

Usable benchmark execution/reporting MVP; reproducing the entire publication, inference farm or all historical analyses is outside this app request.

These are proposed checks, not an executed suite or proof of complete coverage.

| ID | Observable requirement | Concrete oracle / core check | Level |
|---|---|---|---|
| R1 | Keep raw generations and distinct execution outcomes. | Fixtures for syntax error, failing assertion, timeout and pass retain their original text and yield distinct result codes. | integration |
| R2 | Require a runtime-reached meaningful oracle for non-trivial success. | assert True alone, an assertion in an uncalled function, and a skipped assert do not pass the meaningful-oracle gate; a reached exact result assertion does. | unit/integration |
| R3 | Keep oracle strength separate from correctness. | A concrete but wrong equality is specific/strong while execution fails; a result-is-not-None check is weak, not automatically strong. | unit |
| R4 | Use correct aggregation denominators and preserve missingness. | For four eligible tasks with two execution passes, one meaningful pass and one missing result, report 2/4 and 1/4 with the missing task disclosed, not 2/3. | unit |
| R5 | Keep mutation denominators explicit. | For four eligible tasks, two valid suites and one detected fault among one fault per task, unconditional score is 1/4; conditional score is 1/2. | unit |
| R6 | Preserve reproducibility and sandbox restrictions. | Manifest round-trip preserves task IDs/config/hash; sandbox command enforces no network/read-only mounts/timeouts; no training/evaluation files overwritten. | unit/integration |

## Public test boundary (proposal)

CLI/data-record boundaries and an execution adapter; use newly authored tiny fixtures, never paper evaluation task contents.

## Decisions still needing agreement

- Choose one compact task/result schema and the exact missing/infrastructure-error reporting policy.
- Approve oracle taxonomy version and the retained mutation scoring unit.

## Manual / live checks

- Reproduce a small report from saved raw records and inspect table labels.
- Sandbox guarantees need an actual isolation probe; command-string assertions alone are insufficient.

## Candidate existing evidence — not automatically selected

- `tests/test_step4_evaluation/test_oracle_analysis.py`
- `tests/test_step4_evaluation/test_evaluate_results.py`
- `tests/test_step4_evaluation/test_create_realworld_summary_report.py`

Source revision: `380b7d362f49d43fd55af5b2f7e015d4fa651e97`. These prompts are reconstructed drafts, not historical original user messages. Split role is unassigned; never use the same app/scenario for both SFT and claimed held-out improvement.
