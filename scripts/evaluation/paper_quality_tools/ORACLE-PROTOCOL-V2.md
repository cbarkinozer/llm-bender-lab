# Oracle-site review protocol — Version 2 clarification

## Version and provenance note

This version was introduced after both independent rating rounds and after inspection
of their pre-adjudication disagreements. The original ratings were produced under
[`PROTOCOL.md`](PROTOCOL.md), which remains unchanged as Version 1. Version 2 was not
used to revise either rater column. The initial comparison before correction of
confirmed alignment errors yielded 188/250 agreement (75.2%) with unweighted Cohen's
kappa 0.647. After those alignment corrections, the final pre-adjudication Version 1
ratings yielded 190/250 agreement (76.0%) with unweighted Cohen's kappa 0.658.

Version 2 clarifies the unit of classification for constant-truth assertions. It is
intended for future annotation or for a separately identified post-clarification
rerating; it must not be represented as the protocol used for the original independent
ratings.

## Rater task

Independently classify the single oracle identified by `oracle_source`, using its
enclosing test and focal function for context. Do not classify neighboring assertions.
Do not consult classifier output, AI audits, `first_rater_labels.csv`, or result reports
until all 250 ratings are complete.

First record whether the sampled oracle itself depends on a value or state produced by
the system under test in `second_rater_sut_dependent`: `true`, `false`, or `unsure`.
Then assign:

- **TRIVIAL:** statically satisfied, tautological, self-comparison, constant-only, or
  otherwise unable to fail because of focal behavior.
- **WEAK:** depends on focal behavior but checks only a coarse property such as
  existence, truthiness, non-nullness, type, non-emptiness, or a broad shape/property.
- **STRONG:** checks a specific behavioral contract: expected value/content, precise
  state transition, expected exception/warning, or a verified mock interaction tied
  to focal behavior.
- **UNKNOWN:** the shown evidence is insufficient to determine dependency or strength
  safely. Explain the unresolved provenance or ambiguity; do not use UNKNOWN merely
  because classification is difficult.

For compound predicates, classify by the strongest meaningful SUT-dependent branch;
if provenance cannot be resolved, use UNKNOWN. An assertion about mocked state is
STRONG only when the mock is demonstrably the relevant dependency. A specific-looking
comparison that is not connected to focal output/state is UNKNOWN or TRIVIAL, not
automatically STRONG.

Apply these edge cases consistently:

- Classify the sampled oracle itself, not the test as a whole. An unconditional
  assertion whose evaluated predicate is a constant truthy value (for example,
  `assert True`, `assert 1`, `assert "x"`, or `self.assertTrue(True)`) is TRIVIAL
  because the assertion cannot distinguish correct from incorrect focal behavior.
  This remains true when a focal call precedes it. Reaching the assertion may show
  that preceding code did not raise, but that evidence belongs to the execution
  outcome and does not make the constant assertion non-trivial. Constant-only
  comparisons such as `assert [] == []` are likewise TRIVIAL.
- `assert x`, `assert x is not None`, type-only checks, and `assert len(x) > 0` are
  normally WEAK when `x` is SUT-derived; they are TRIVIAL when statically guaranteed.
- Equality to a literal or independently computed expected value is STRONG when it
  expresses a specific focal contract. Equality between a value and itself is TRIVIAL.
- `pytest.raises(ExpectedError)` and `pytest.warns(ExpectedWarning)` are STRONG only
  when the enclosed focal action is what must raise/warn. An empty or unrelated block
  is UNKNOWN/TRIVIAL as appropriate.
- `assert_called*`, `assert_awaited*`, and equivalent mock checks are STRONG only when
  the mock is a dependency exercised by the focal function; checking setup state alone
  is TRIVIAL.
- An assertion located in a statically unreachable branch is TRIVIAL for runtime-gate
  purposes. If reachability depends on unavailable runtime facts, use UNKNOWN and note it.
- Parametrization changes inputs, not oracle strength. Rate the sampled oracle site once
  based on the contract it expresses across parameters.
- For helper assertion functions, follow the helper only when its behavior is present
  in the supplied evidence; otherwise use UNKNOWN rather than guessing.
- When a test contains multiple assertions, rate only the sampled `oracle_id`. A
  compound assertion is one site; separate assertion statements are separate sites.
- Static presence and runtime execution are distinct. The class describes the sampled
  oracle's semantics; `second_rater_sut_dependent` records provenance. Do not infer that
  an oracle executed merely because it is statically present.

If the required source is missing, use `NOT_RATEABLE_MISSING_EVIDENCE`; this is an
administrative exclusion. Reserve UNKNOWN for a present oracle whose semantics or SUT
provenance cannot safely be resolved.

Record confidence (`high`, `medium`, `low`) and notes for every UNKNOWN, UNSURE,
NOT_RATEABLE, or low-confidence decision. Before returning the file, confirm all 250
rows are rated and that row IDs/order are unchanged.
