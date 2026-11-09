# Semantic coverage audit of the 50 training targets

Date: 2026-11-07. CPU static analysis only; no generated or target test code was
executed on the host during this audit. Machine-readable detail with one record
per target is in `semantic-coverage-audit.json` (same directory).

## What this audit answers

`NEXT-PAIR-PLAN.md` set a gate before any Exp3/Exp4 run: complete a genuine
semantic coverage audit of the fifty TRAINING targets, mapping each requirement
to a justified oracle and checking real-SUT fidelity plus positive/negative
controls. The earlier `training-target-inventory.json` measured only compact
style (function/line/assert counts) and explicitly deferred this question.

## Scope and parity

- Source: `quality-audit-v01/current-test-candidates.jsonl`
  (sha256 `9feec86f910e274f0a9d4703a512d2acce08b97e0a86b1e63cc7abc0f01020cd`,
  the same file the inventory hashed).
- 50 train rows = 38 `task-to-tests` (structured `acceptance_criteria`) +
  12 `task-test` (requirements embedded in the prompt's acceptance contract).
- Parity confirmed: the 50 audited record ids are exactly the record ids in
  both `paired-preflight-v02/A/train-encoded.jsonl` and `.../B/train-encoded.jsonl`.
  The audit therefore covers the data that was actually trained in both arms.

## Method

For each authored target artifact: AST parse (not execution) to check that the
real implementation module is imported rather than shadowed by a locally defined
stub, to classify builder helpers vs fixtures vs test functions, to check
`parametrize` argname/value arity, and to see what each `Mock`/`monkeypatch`
substitutes. Positive and negative controls are read from the validation runs
already recorded in the dataset: the `reference` and `order-*` shuffle runs are
positive controls (must pass), and each named behavioral mutation is a negative
control (must be killed).

## Result — gate PASSES

All 50 targets clear every automated check. No target required repair.

| Check | Result |
|---|---|
| Parse cleanly | 50 / 50 |
| Import the real SUT module | 50 / 50 |
| Local stub shadowing a SUT symbol | 0 / 50 |
| `parametrize` arity / signature defects | 0 / 50 |
| Reference (positive control) passes | 50 / 50 |
| Order-shuffle robustness (3 seeds each) passes | 50 / 50 |
| At least one killed mutation (negative control) | 50 / 50 |
| Mutations that survived (control gap) | 0 / 50 |

Negative-control depth: 29 targets kill one named mutation, 21 kill two. Every
mutation name maps directly to a stated requirement, e.g. cumulative-not-daily
returns -> `daily-instead-of-cumulative`; config swap takes effect ->
`cache-initial-configuration`; Macro-F1 counts the unpredicted class ->
`f1-equals-accuracy`; future tokens cannot change earlier logits ->
`remove-causal-mask`; verbosity suffix parsed -> `lose-verbosity`.

This is the opposite profile from the five development candidates (model outputs),
which failed on missing imports, locally redefined SUT functions, broken
`parametrize` arity, unrelated filesystem assertions and non-collected tests.
Those defects do not appear in the training targets.

## Why the flagged helpers are not defects

- `make_app`, `prices`, `mail`, `choice`, `model`, `config`, `rows`, `trainer`
  are Arrange-phase builder functions that construct inputs or inject fake
  dependencies. None redefines a SUT symbol (`shadowing_sut_stubs` is empty for
  all 50). Contrast candidate B in the dev set, which redefined
  `extract_path_param_names` locally and tested nothing real.
- Mocks and `monkeypatch` isolate dependencies or control environment/inputs
  (`sys.argv`, `sys.stdin`, `sys.platform`, `XDG_CACHE_HOME`/`HOME`, a command
  registry) or isolate a sibling function in a multi-function module. No target
  mocks the exact function it asserts on, so coverage is real.
- A Turkish name in a `ghost-box` fixture renders as mojibake only in a cp1252
  console; the file is UTF-8. Not a data defect.

## Qualifications (not blockers)

- Several targets state more requirements (2-4) than they have dedicated
  adversarial mutations, so not every individual requirement has its own
  negative control. The passing reference oracles still assert those behaviors.
  This is coverage depth, not a correctness defect. Per the plan, no minimum
  mutation/function/line count is introduced as a coverage substitute.
- The 12 lean `task-test` rows keep requirements in prose rather than a
  structured array. They are among the best-controlled (2 killed mutations each).
  Normalizing them to the richer schema when versioning data for Exp3/Exp4 is a
  consistency improvement, not a correctness fix.

## Consequence for Exp3 / Exp4

The audit passes with no substantive data change, which satisfies the plan's
condition to proceed with the learning-rate pair (Exp3 1e-5 vs Exp4 3e-5,
B-style loss) on the **same 50 audited rows**. Because the training data is
unchanged, the historical Arm-B at 1e-4 remains a clean learning-rate-only
comparator. Remaining preparation (versioned manifests, token arrays, masks,
runtime gates, GPU access) is still pending and unchanged by this audit.
