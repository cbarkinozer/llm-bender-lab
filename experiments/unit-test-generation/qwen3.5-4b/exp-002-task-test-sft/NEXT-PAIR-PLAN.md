# Next pair proposal after inspecting all five questions

Status 2026-11-07: diagnosis and proposal only. Exp3/Exp4 manifests, new data,
revised evaluation prompts and GPU runs have not been prepared. Current primary
responses, requirements, reference tests and scores remain unchanged.

## Evidence and provenance

All five supplied requirements and all fifteen displayed candidate files were read
alongside the complete submitted evaluation descriptions. The user clarified that
these descriptions are LLM evaluations. Treat them as LLM-assisted judgments submitted
through the user's Argilla account, not independently validated human ground truth.
Original submissions are preserved. No agreement statistic between humans is justified.

The descriptions correctly identify many concrete defects, but contain assumptions
and informal smell labels. Record a separate interpretation instead of silently
correcting the saved labels or accepting every criticism as a proven contract breach.
The prior overall conclusion still holds: no executable utility gain was demonstrated.
Base has the preferred submitted ranking on four cases, yet all models have zero
complete reference-passing suites. A causal claim of catastrophic forgetting or
excessive learning rate is not established by this result.

This inspection is static. Existing protected execution logs provide runtime evidence;
no generated candidate code was run on the host or newly executed during this pass.
Authored development reference tests were read as audit evidence, not model context.

## Case-by-case inspection

### 1. Path parameters

Confirmed in candidate code:

- B defines functions named like the SUT rather than test functions. Its decorator
  is attached to a non-test function, so it has no normal pytest test functions.
  It uses brace placeholders despite the colon-placeholder requirement and uses a
  set comparison that loses ordering information.
- A imports the real functions but expects pairs such as `('foo', 'bar')` without
  justification from the supplied interface. Its single substitution example is
  consistent with replacement and escaped-colon handling.
- Base omits the imported SUT functions. Some escape/replacement expectations also
  contradict its own URL inputs, including dropping a slash and duplicating `v1`.

Qualification of the LLM description:

- Bare names versus colon-prefixed names is not explicit in the request. Authored
  reference tests expect bare names; this is hidden reference knowledge until the
  interface is clarified.
- The request says names START with a letter or underscore; it does not fully define
  subsequent characters. The review's claim that `:my-param` must stop at `my` is
  not established by that sentence alone. The generated test's own docstring is not
  an authoritative requirement. Define a complete name grammar before scoring this.

Next-protocol candidate: explicit `list[str]` return schema, colon inclusion policy,
complete character grammar, and the existing escaping/query/fragment rules.

### 2. Query-pair merge

Confirmed in candidate code:

- A declares two parametrized argument names but supplies three values. It supplies
  pairs rather than the explicitly requested enabled triples, and checks the
  original query-bearing URL rather than the required stripped URL.
- B defines local functions bearing the SUT names, never imports the module, decorates
  a test whose signature does not accept the parametrized arguments, and asserts a
  temporary path exists instead of testing query merging. These are clear failures
  of real-SUT testing and pytest construction, not merely subjective smell judgments.
- Base has no complete parseable file in the display packet. Keep that failure in
  the denominator rather than assigning it zero smells as a quality success.

Qualification: the supplied request does not explicitly specify the merge function's
complete return shape, and the ownership of `escape_dollars` is unclear. The authored
reference expects a `(stripped_url, merged_triples)` tuple, and passes escape_dollars
to extract_query_pairs. Clarify those schemas/signatures prospectively. LLM claims
about precise return types require that information; the collection defects do not.

### 3. Request filenames

Confirmed in candidate code:

- A and B use `posting.files...` without importing `posting`. A calls len on the
  validator result and expects suffixes to advance despite no files being created.
- B invents `_filename_counter` and a hardcoded filesystem directory.
- Base uses `patch` without importing it, patches a guessed existence-check seam,
  supplies an always-True existence mock, and checks a terminal numeric suffix even
  though the filename should end in `.posting.yaml`.
- No candidate checks actual CON/NUL/COM1-style examples or the required collision
  sequence using temporary colliding files. No candidate directly establishes that
  the proposal operation leaves directory contents unchanged.

Qualification: `C:` is not itself a reserved Windows device basename. A test of
`C:.txt` does not satisfy the requested device-name coverage, but the review's claim
that accepting it necessarily inverts the contract is too strong. The contract does
not specify all Windows forbidden-character rules or a cross-platform path policy.
Native separators are platform-sensitive; filename-validation input strings are not
automatically live external I/O or Fragile Test defects.

Next-protocol candidate: explicit bool return, separator/platform policy, basename
versus path return, input-name extension policy, and stateless collision semantics.
The authored reference passes an already suffixed filename and expects a basename;
do not conceal those assumptions from a future evaluated model.

### 4. Session undo/redo

Confirmed in candidate code:

- B uses `.get()` and `.edit()` methods not supplied in the public interface.
- A asserts an undocumented set return value, reads a removed override as an empty
  string, and expects redo to be unavailable immediately after undo.
- Base contains useful state assertions but also expects undo to clear redo and
  makes contradictory assumptions about undo after revert.

Qualification: explicitly settle whether revert is an undoable editor edit and
whether absent-name revert changes history/redo. The authored reference treats
successful revert as undoable. A generated test should not have to infer this from
hidden code. Repeated set/undo/redo calls are often necessary for the specified
state transitions, so an eager-test flag is not sufficient grounds to remove them.

### 5. History retention and script writes

Confirmed in candidate code:

- A inspects the forbidden `.history` API, assumes undo increases it, never performs
  the requested script write, and makes an impossible history-length progression.
- B calls values as a method, writes to the SessionVariables object rather than
  its values mapping, and uses `undo() * 70` instead of making seventy undo calls.
- Base also calls values as a method and writes arbitrary attributes instead of
  values. It confuses retention of edit history with deleting current values and
  asserts the edited value after an undo intended to restore the earlier state.

Qualification: make `values` an explicitly mutable public mapping and define the
non-string/script snapshot semantics. Distinguish an undo-history cap from a cap
on the number of current variables. Constants 50/51 are specified boundaries, not
automatically unjustified magic values. Boundary tests require >50 edits and then
undoing past the retained boundary, not just checking a container length.

## What this suggests about training

A static inventory of the actual fifty train targets is in
`next-pair-diagnosis-v01/training-target-inventory.json`:

- 106 recognized test functions: mean 2.12 per file, median 2, range 1-5.
- Mean 26.52 source lines per target, median 21.5, range 11-77.
- 198 plain assert sites. This excludes other oracle forms, so zero plain asserts
  does not imply no oracle.

This is consistent with a compact output style, but DOES NOT establish inadequate
requirement coverage. A short parametrized file or stateful sequence can cover many
requirements. The fifty targets have prior executable checks; a new full semantic
coverage review of all fifty has NOT been completed in this turn.

The next CPU audit should map each training acceptance requirement to a justified
oracle, inspect external mocks versus real SUT imports, and check positive/negative
controls and public API fidelity. Use these generic failure classes to design the
audit, without copying corrected Posting examples or review-derived desired outputs
into training. No minimum function count, line count or rationale length should be
introduced as a substitute for behavioral coverage.

The stored planning and clarification/integrity tracks were not part of either
fifty-row training run. Their existence in the dataset inventory is not evidence
that these adapters were taught clarification, replanning or explicit anti-cheating
behavior. Adding those tracks would be a separate intervention, not an LR-only pair.

## Proposed Exp3 / Exp4

If the CPU audit passes without a substantive data change, use a learning-rate pair:

| Setting | Exp3 | Exp4 |
|---|---|---|
| Peak learning rate | 1e-5 | 3e-5 |
| Starting checkpoint | Fresh pinned original base | Same |
| Loss objective | B-style answer loss; rationale-text labels masked | Same |
| Teacher-forced input | Original complete input, including rationale | Same |
| Training rows | Same fifty audited rows | Same |
| Epochs / updates | 3 / 21 | Same |
| LoRA rank / alpha / dropout | 16 / 16 / 0 | Same |
| Batch / accumulation | 1 / 8 | Same |
| Seed, scheduler, warmup, optimizer, inference | Frozen previous settings | Same |

This tests gentler adaptation, not whether rationale-free training is better.
B's marginal review advantage does not establish that its objective is superior.
Exact rates are engineering hypotheses, not known optimal settings.

If the audit finds material target issues, fix and version those first; use the
same corrected dataset in both new arms and document that the previous B run is
no longer a clean learning-rate-only control. Do not launch training merely to
finish an already prepared pod while the data question is unresolved.

Evaluation-contract clarifications above are PROPOSALS, not silently adopted user
requirements. Freeze the intended semantics, update references/controls consistently,
and run a new common base if measured prompts change. That revision is an adaptive
development benchmark informed by observed failures, not fresh held-out evidence.
Preserve old five-case submissions/scores unchanged. Reserved holdout inference and
scoring remain untouched; no development repairs enter training.

Keep complete-reference passing and gated fault credit primary. Add per-case coverage,
collection errors and optionally per-test outcomes as secondary diagnostics to explain
the all-zero suite floor; do not rescue bad suites by dropping failures or crediting
one trivial passing assertion. Keep smell/oracle labels exploratory. Compare new
outputs anonymously and record the reviewer's exposure to the previous cases.
Preselect final checkpoints; epoch inspection is exploratory. If both gentler arms
still lose, stop the LR sweep and reconsider target/task design.

## Immediate remaining work

1. Complete the semantic coverage audit of fifty training targets.
2. Resolve and freeze the intended interface declarations for the next dev revision.
3. Prepare separate versioned Exp3/Exp4 manifests, masks and runtime gates.
4. Request/verify a GPU only after CPU gates; shared baseline first if prompts change.
5. Run both arms, infer with identical settings, protected-grade and download all
   adapters/logs/results before closing compute. Do a new anonymous comparison.

Downloads handoff: `C:/Users/barkin/Downloads/CLAUDE-HANDOFF-llm-bender-tdd-20261107.txt`.
Companion: `tdd-five-cases-with-llm-reviews-20261107.txt` in the same Downloads folder
contains all five original requests, fifteen displayed outputs, primary identity
mapping and exact LLM descriptions. It is unblinded analysis material, not a packet
for an independent blind grader. No credentials or supporting private mappings
are included in either file.
