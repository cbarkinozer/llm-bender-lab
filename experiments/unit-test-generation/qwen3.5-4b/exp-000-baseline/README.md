# exp-000-baseline

Current: [Stage A v01](requirements-pilot/STAGE-A-V01.md) generation settings are
frozen. TOML reference defect confirmed/quarantined; Mashumaro reference validated,
one new original suite generated and prepared for independent owner review.
The complete 20-task benchmark and implementation comparison remain unfrozen.

## Status

Development pilot underway; no frozen benchmark scores or training results.
DeepSWE download/hash and descriptive EDA are complete. Twenty tasks from distinct
repositories are provisionally shortlisted. A first requirement-only Pi generation
smoke has run; later thinking-enabled tests pass 16/20 against the reference but
remain rejected. Direct generated code passes 4/60 hidden feature tests and
964/964 regressions. These are single-task diagnostics with differing conditions,
not a controlled effect estimate. A suspected reference defect needs adjudication.
See the pilot report.

## Question and comparisons

Can untouched Qwen3.5-4B Q4_K_M generate requirement-faithful tests through Pi,
and does a test-first workflow improve independently measured implementation
correctness over direct code generation? Follow the
[requirements-first protocol](../REQUIREMENTS-FIRST-PROTOCOL.md).

Compare direct-code and prompted-TDD conditions under matched total budgets.
Test generation cannot see reference implementations or private grading data.
Stage A reviews and freezes tests; Stage B implements with those tests read-only.
Human assistance and failures are recorded separately from autonomous performance.

## Artifacts and evaluation

`config-planned.json` remains a non-executable planning record. Existing pinned
model/runtime references and the Q4_K_M artifact hash are preserved. Formal
context/token/time/repair budgets and task environments are not frozen yet.

- `benchmark-audit/deep-swe-20261017/`: source inventory, hash and descriptive EDA.
- `requirements-pilot/candidate-manifest.json`: 20 provisional tasks, exclusions,
  prompt hashes and external packet paths. DeepSWE is evaluation data, never training.
- `requirements-pilot/`: smoke evidence and static requirement-alignment review.

Report test semantics/importance, the owner's oracle/smell taxonomy, execution
health and independent hidden implementation correctness separately. Generated
suite passing alone is insufficient. Do not silently repair scored originals.

## Next step

Validate one task's contract/interface and reference environment, inspect original
smoke suites, then finish protected frozen-test implementation and hidden grading
before expanding to 20 paired episodes. SFT and SFT+GRPO are later experiments
using separate validated training demonstrations/tasks.
