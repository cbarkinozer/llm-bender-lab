# Test quality review rubric v0.1 — development draft

Derived from the owner's `tests-that-run-but-do-not-test-paper.tex` and early
thesis; source hashes are in exp-000-baseline/environment-mac.json. This draft
needs development calibration before use as a frozen metric or training reward.

## Independent outcomes

Record execution validity, oracle reachability, semantic correctness, quality
dimensions and smells separately. A passing suite need not be useful. A specific
oracle need not encode a correct expectation. Human repairs never replace the
original model output in scoring.

## Oracle-site annotation

| Class | Criterion | Example |
|---|---|---|
| TRIVIAL | SUT-independent and statically satisfied | `assert True` |
| WEAK | Coarse SUT-derived truthiness, nullity, existence or type | `assert result is not None` |
| STRONG | Specific expected value/content/range, exception/warning, state or interaction contract | `assert result == expected` |
| UNKNOWN | Insufficient evidence to resolve semantics or provenance | `assert helper(result)` |

For each oracle also record SUT dependence, whether it executed, semantic
correctness, confidence and evidence. Exception contexts and mock interaction
checks count as oracle sites; mock checks must relate to the intended contract.
Missing evidence is not automatically a substantive UNKNOWN label.

Runtime non-trivial success requires a passing suite and at least one reached
WEAK/STRONG oracle. This is a gate, not an assertion that the suite is adequate.

## Suite ratings, 1–5

| Dimension | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Robustness | Critical scenarios missing | Standard happy path only | Some meaningful variation | Multiple relevant edge cases | Comprehensive relevant boundaries and behaviors |
| Assertion strength | Absent/trivial | Generic/coarse | Basic correctness checks | Specific key-behavior checks | Strong specific checks of relevant values/state/exceptions |
| Readability | Confusing | Unclear structure | Understandable | Clear intent/structure | Clear names and professional structure |
| Conciseness | Dead/redundant complexity | Notable redundancy | Some unnecessary code | Little redundancy | Efficient without omitting needed checks |

Rate robustness against the documented contract, not a universal checklist of
None, negative inputs and type errors. Do not reward exact equality when tolerance
is appropriate, or shortness that removes valuable cases. Record not-rateable
dimensions explicitly; preserve failures in the evaluation denominator.

## Smell review

Review Assertion Roulette, Eager Test, Mystery Guest, Magic Number Test, Obscure
Test, Lack of Cohesion, Conditional Test Logic, External Dependency, Unverified
Action, Trivial Assertion and Duplicated Setup. Record affected location,
evidence, severity and maintenance/behavioral impact, not only counts.

Static detectors propose candidates. Missing assertion messages are not by
themselves an actionable smell under pytest; several calls may form one coherent
scenario; filesystem/network dependencies may be safely isolated; loops and
parameterization can improve testing. Weak nullity checks are WEAK in the newer
oracle taxonomy, even if the older smell terminology used “trivial” more broadly.

## Review protocol

First rate blind to model identity and LLM suggestions, then inspect suggestions
and retain separate adjudicated decisions. Use repeated/swapped controls during
development. Validate judge and classifier on new tasks rather than importing
the paper's historical reliability claims. Primary aggregation, weights,
acceptance thresholds and reward are deliberately not selected in this draft.
