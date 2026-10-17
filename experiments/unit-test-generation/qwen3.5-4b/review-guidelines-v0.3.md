# Review guidelines v0.3 — development calibration

Python / pytest; requirement-first test generation. Language and instructions are
shown separately from verified existing API facts. Numbered clauses are a reviewer
aid, not a rewritten specification or evidence that an ambiguity is resolved.
The verbatim model context is retained for audit because it originally mixed facts
and instructions. Future prompt changes require a new generation protocol.

## Pass@1

Use one original generation per task with no repairs or best-of-k selection.
Report execution Pass@1 (whole suite passes the validated reference) separately
from runtime non-trivial Pass@1 (also reaches at least one WEAK/STRONG oracle).
Do not report the runtime gate until oracle reachability has been measured.
Neither metric establishes semantic adequacy. Report important behavior coverage,
correctness, smells and cost separately; no arbitrary composite score.
Show eligible-task counts and all candidate statuses. Infrastructure failures are
unresolved, never silently counted as model successes/failures; quarantined tasks
remain visible. Human repairs never improve original Pass@1.

## Per-test rows

Use one line per test (parameter cases may differ), with this template:
`test_name | R IDs | alignment | oracle sites/classes | smells | reason`
Alignment: justified / incorrect / assumption-under-ambiguity /
irrelevant-to-requirement / uncertain. Multiple findings may coexist in one test;
identify assertion lines where they differ. Oracle class describes each oracle,
not the whole test. Use TRIVIAL / WEAK / STRONG / UNKNOWN; NO_ORACLE means no oracle
site, rather than an extra assertion class. Track reachability separately later.
An exact but wrong assertion may be STRONG and incorrect. A `pytest.raises` block
containing only `pass` is a failing exception oracle, not an oracle-free test.

For each R ID, record covered / partial / missing / tested-wrongly / uncertain,
with test references. Multiple equivalent tests do not increase clause coverage.
State protected and missing important behavior without inventing new requirements.
Smells require location and concrete harm under the owner's eleven categories;
other defects belong in alignment/evidence rather than forced smell mappings.

## Calibration examples for the existing 1–5 scale

These are illustrative anchors, not automatic scores from counts.

| Score | Robustness | Assertion strength | Readability | Conciseness |
|---|---|---|---|---|
| 1 | Main flatten behavior absent | Only constant assertions | Intent cannot be reconstructed | Extensive unrelated/dead setup |
| 2 | Basic happy path only | Only dict/type existence | Names obscure expected behavior | Repeated scenarios and unused setup |
| 3 | Happy path plus a meaningful variant | Some expected values, major outcomes unchecked | Understandable with effort | Useful suite with some redundancy |
| 4 | Core behaviors and relevant boundaries | Specific checks for key behavior | Clear scenario names and setup | Little unnecessary duplication |
| 5 | All important explicit contract behaviors and relevant boundaries | Specific discriminating checks across relevant outcomes | Consistently clear intent and structure | Minimal redundancy without losing protection |

Rate dimensions separately from semantic correctness. A small suite can be clear
and concise yet incomplete. Mutation detection is supporting evidence, not a
replacement for human assertion-strength judgment or specification correctness.

Retain: original suite usable as-is for its stated scope. Repair: useful parts
exist but original needs changes. Reject: unsuitable as a suite; individual useful
tests may still be retained separately. Uncertain: insufficient evidence.
No percentage-of-salvageable-tests cutoff is imposed. Proposed repair notes are
optional during initial review; actual repaired code must be saved separately with
its source run, author, change rationale and validation before use as SFT data.
DeepSWE examples and their repairs remain evaluation/development artifacts, not SFT data.

Confidence: high = explicit contract/API evidence resolves the judgment;
medium = localized uncertainty; low = major specification/API uncertainty.
Use not-rateable when a dimension cannot reasonably be assessed.

## Assisted review and later evidence

Owner and assistant may discuss and adjudicate together. Record this as assisted
human review, not independent raters or inter-rater agreement. Preserve initial
judgments when available, then save evidence-assisted decisions separately.
This Mashumaro example has already received external AI feedback and is calibration.
Model identity and execution outcomes remain outside this first review view.
Later evidence includes collection, per-case reference results, oracle reachability
and targeted mutants. Reference failures require adjudication, not automatic blame
on the model. Do not infer runtime oracle success from AST presence alone.
