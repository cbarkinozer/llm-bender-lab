# Primary review and algorithmic quality results - 2026-11-07

The current pair does not demonstrate improved useful test generation. The submitted
blind review prefers base on four of five development cases. Both adapters tie above
base on the query-merge case, but all three outputs for that case are rejected.
No candidate in the entire 15-output comparison was marked retain.

## Submitted primary review

| Model | Sole best | Tied best | Retain | Repair | Reject |
|---|---:|---:|---:|---:|---:|
| Base | 4 | 0 | 0 | 3 | 2 |
| Exp1 / A: rationale + answer loss | 0 | 1 | 0 | 0 | 5 |
| Exp2 / B: rationale labels masked | 0 | 1 | 0 | 1 | 4 |

| Task | Submitted ordering, best first |
|---|---|
| Path parameters | Base > A > B |
| Query-pair merge | A = B > Base; all rejected |
| Request filenames | Base > B > A |
| Session undo/redo | Base > B > A |
| Session history limit | Base > A = B; all rejected |

B is preferred to A on two cases, A to B on one, with two ties. This is a small,
single-family, single-submitted-review diagnostic; it does not establish a general
winner or reliable effect size. No evidence that rationale supervision helps here.
The exported review is user-submitted; no claim of independent external human review,
inter-rater reliability, or known absence of AI assistance is made.

## Existing execution and generation evidence

These are the saved, previously protected execution results, not a new execution run.

| Measure | Base | Exp1 / A | Exp2 / B |
|---|---:|---:|---:|
| Correct-reference-passing suites | 0/5 | 0/5 | 0/5 |
| Credited targeted faults | 0/10 | 0/10 | 0/10 |
| Strict format checks | 2/5 | 5/5 | 4/5 |
| Primary output tokens, including thinking | 30,990 | 1,282 | 2,261 |
| Output-cap truncations across nine requests | 1 | 0 | 0 |

Reference success gates fault credit; tests that fail everywhere do not earn credit.
The protected authored controls passed 5/5 and caught 10/10 injected faults. Both
adapters terminate normally and use substantially fewer tokens, but their wrong APIs,
expectations and collection errors prevent a correctness improvement. The base
truncation was progressive output, not evidence of a repetitive loop. Primary static
format failure also prevented execution of some base/B files; all are retained in
output accounting. Formatting and compilation are not equivalent to useful tests.

## Algorithmic smells using the requested paper checkout

Executed detector definitions from
`C:/Users/barkin/Documents/GitHub/slm_test_generation/step4_evaluation/analyze_test_smells.py`,
commit `380b7d362f49d43fd55af5b2f7e015d4fa651e97`, excluding plotting and the corpus runner.
The checkout's oracle classifier matches the frozen vendored version. Source hashes
and executed extraction hash are in the machine-readable summary. No paper samples,
applications, tests or requirements were ingested. No generated code was executed.

We call the original analyze_test_code for EACH focal function/method explicitly
named in the supplied interface and union its flags. This fixes the earlier adapter's
incomplete eager-test detection for object methods (set/undo/redo/revert). It does not
change the paper detector definitions or thresholds. Earlier v02 diagnostics remain
preserved, rather than being silently overwritten.

Counts below are FILES flagged, not confirmed defects. Denominators are parseable
files with recognized test functions: base 4, A 5, B 4. Base's one incomplete output
and B's one zero-test-function output are separate failures, never smell-free passes.

| Smell | Base (of 4) | A (of 5) | B (of 4) |
|---|---:|---:|---:|
| assertion roulette | 4 | 4 | 2 |
| eager test | 3 | 4 | 3 |
| mystery guest | 0 | 0 | 0 |
| magic number test | 1 | 2 | 1 |
| obscure test | 0 | 0 | 1 |
| general fixture | 0 | 0 | 0 |
| conditional test logic | 3 | 1 | 1 |
| fragile test | 1 | 0 | 1 |
| unknown test | 0 | 0 | 0 |
| trivial assertion | 2 | 0 | 0 |
| duplicated setup | 2 | 0 | 0 |

Files with any flag: base 4/4, A 4/5, B 3/4. These counts are NOT a quality ranking:
base has 48 recognized static test functions, A 8, B 15, so opportunities differ.

Concrete interpretation limits from this run:

- Eager-test flags on repeated set/undo/redo calls can reflect necessary stateful testing.
- Magic-number flags include 50/51 and 256, which are specified history/filename boundaries.
- Base's fragile flag on `C:\Users\File` is a filename-validation INPUT, not proof of
  an environmental dependency. B's `/tmp/sessions/` flag concerns an actual proposed
  directory argument and is more actionable.
- Duplicate-setup detection also flags repeated `result = ...` behavior calls; these
  are not necessarily duplicated fixture setup.
- Pytest assertion introspection can make message-free assertions understandable;
  assertion roulette is a heuristic here, not proof of unusable failure diagnostics.
- Zero obscure flags for base does not refute the submitted review's concerns about
  speculative comments: the algorithm measures AST statement/assignment thresholds.
- Initial free-text review uses some smell names informally. It is not an independent
  per-category annotation sheet, so no human-machine agreement statistic is calculated.

## Automatic oracle taxonomy

| Model | TRIVIAL | WEAK | STRONG | UNKNOWN | Sites |
|---|---:|---:|---:|---:|---:|
| Base | 0 | 1 | 22 | 70 | 93 |
| A | 0 | 0 | 5 | 34 | 39 |
| B | 0 | 0 | 6 | 30 | 36 |

134 of 168 sites are UNKNOWN: the function-oriented classifier cannot establish
provenance through many full-file imports, objects and helper contexts. Raw assertions
missed by its traversal remain included as UNKNOWN, not dropped. No runtime-reached
oracle claim is made. STRONG is structural specificity, not requirement correctness;
a precise wrong expectation may still be classified STRONG. These outputs cannot
support an assertion-strength winner or a validated non-trivial/strong pass metric.

## Decision and next work

Do not promote A or B as a utility improvement. Keep the pair as evidence that this
small, compact-target SFT recipe changes length/format without demonstrated useful
behavior. B is only slightly less poor in this local review; its relative result is
not enough to choose a superior rationale-training objective.

Before another GPU pair, audit the training targets for coverage of their own
requirements, public API fidelity, pytest collection and useful positive/negative
controls. Existing reference validation passes, so this is a coverage/style audit,
not an assertion that the training labels have been found broken. Investigate whether
the compact target style teaches compressed examples at the expense of adequate
behavioral coverage. Retain the current reference-pass and fault-credit gates.

The submitted review also identified under-specified contract details: colon inclusion
in extracted parameter names, bare filename versus directory-prefixed return, and
whether revert is itself undoable. Clarify those in a NEW protocol revision before
using them for a new measured comparison; keep this run's prompts, labels, references
and scores unchanged. Regenerate the same shared baseline if prompts change.

The owner waived exhaustive manual oracle and smell annotation for this demo. The
five completed primary reviews alone gate this report; skipped labels are not invented.
Automatic findings remain unvalidated diagnostics. Supporting probes remain unreviewed
in this report, and the reserved holdout remains unopened. No further manual 169-site
annotation is required to complete this primary demo assessment.

## Artifacts

- `gpu-results-20261107/post-review-v01/summary.json`: aggregates, protocol amendment, hashes.
- `submitted-primary-review.json` in that folder: exact submitted evidence, ranks and assessments
  mapped to primary model identities; no account identifiers or private supporting mappings.
- `automatic-per-candidate.json`: all fifteen static analyses and detector evidence.
- `verification.json`: full replay, exact original display-field match, controls and ten tests.
- Raw primary freeze and receipt: external artifact root under
  `argilla-exports/post-review-v01/`; preserved before unblinding.
- Reproduce with `scripts/evaluation/summarize_tdd_demo_review.py --snapshot <v02-export>`;
  choose a new `--output` for each new version. It refuses overwriting earlier reports.
