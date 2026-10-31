# Adjudication of the v06 static AI review — 2026-10-31

This audits the review against the exact v06 messages and supplied annotation
guidelines. It is a second assistant's assessment, not a new human annotation or
replacement of the original review. No dataset messages, splits or approvals
were changed. The revision-07 corrections and their validation remain separate.

## Conclusion

The review was useful and identified real behavioral gaps, but several rationales
overstated evidence or promoted editorial preferences into blockers. Its 1 approve /
8 revise is a workflow verdict under a strict rubric, not an estimate that eight
examples were mostly incorrect. Correcting a faulty rationale does not automatically
approve the affected record: most still had independent valid issues.

## Findings requiring correction or qualification

| Review finding | Adjudication | Reason |
|---|---|---|
| "new public/shared facade" proves review/meta leakage | Unsupported classification | In a proposed-interface answer, "new" can simply mean a component to implement. It does not establish a hidden codebase, revision commentary or grading leakage. The supplied guidelines permit explicitly proposed APIs. Removing unnecessary framing is harmless editing, not evidence of corrected contamination. |
| GitHub activity-window interpretation must be moved into Decisions | Redundant as an interface-sufficiency blocker | v06 interface.md line 4 already defines the same UTC date twelve months earlier, leap-day clamping and end=now. The rubric accepts decisions in input OR target agreement; it does not require duplication between sections. |
| GitHub Origin 403 / Host 400 choice is undeclared until moved to Decisions | Overstated | v06 interface.md line 7 explicitly declares those statuses. Explaining their purpose is useful, but relocating already visible text is an editorial improvement. Other GitHub gaps, such as exact sort values and auth schema, remain valid. |
| Paths mentioning v05 mean stale fault evidence | Not established; the actual request to confirm was reasonable | All eight siblings of codelang-detect have byte-identical Python tests, reference modules AND model messages in v05/v06. Old paths are not proof that changed tests were evaluated. Environment equivalence is a separate issue. The actual review mostly asks for confirmation; its summary's "stale" wording is stronger than the evidence. v07 has fresh runs regardless. |
| Deterministic if/elif fixture mutation is automatically a harmful smell | Preference overstated | The GitHub case is already parametrized; the branches select a known defect rather than reproduce the SUT's decision logic. Parametrized mutators simplify it, but concrete harm is needed for an actionable smell. By contrast, the research-runner conditional genuinely omitted a positive nontrivial-gate assertion, so that finding was valid. |
| A combined MCP/HTTP/security test necessarily has poor failure diagnosis | Optional restructuring | Separate tests improve isolation, but pytest's exact failing assertion already identifies the broken check. The rubric explicitly says related assertions are not automatically poor diagnosis. No concrete ambiguity was demonstrated. |
| Half-second timeout may include Docker startup | Mechanism needs qualification | v06's supervisor applies timeout_seconds to the pytest subprocess; the outer container gets timeout_seconds+15. The 0.5-second pytest budget is still fragile because it includes pytest startup/collection. The missing local-executor seam is a real contradiction between the decisions and actual signature. |
| reached_oracles must use first-reached order | Added requirement | v06 tests only require [] when nothing is reached. They do not imply event-order semantics. The reference returns sorted unique IDs. Declaring a list is useful; requiring first-reached order is arbitrary. v07 correctly declares sorted unique IDs. |
| Underscore helper names alone prove undeclared/private coupling | Partly overstated | The cryptocurrency helpers are explicitly declared in the target agreement, and separation of calculation/I/O is part of the request. They are not hidden solely because of underscores. Pinning unnecessary orchestration details is a reasonable concern; public naming improves the teaching contract but does not itself establish better coverage. |
| Miniature components require separate public constructors and isolated numeric tests | Stricter than necessarily required | The request asks for modular working components but does not require a separate public constructor per component. v06 does test composed-model causality, gradients and checkpoint behavior. Standalone component coverage is a legitimate limitation; explicit disclosure is reasonable and is one of the review's offered alternatives. |
| Source relevance=yes with high confidence across all nine | Evidence limitation | The reviewer expressly did not inspect source repositories. It can assess request/target consistency, but cannot independently certify source-repository fidelity. The source-relevance anchor offers uncertain when source evidence is unavailable. This does not invalidate its directly observable code findings. |

## Findings confirmed as real

- **Cryptocurrency baseline contradiction:** request.md says first observed price;
  interface.md and the NaN-first-row test reject a valid later first observation.
  The request takes precedence over an assistant-proposed decision. This is an
  actual correctness issue, not a style disagreement.
- **ReflexModels missing acceptance control:** v06 tests fallback-required=True,
  but never asserts a valid response needs no fallback.
- **Llm-bender split routing:** checking equal baseline/candidate rows does not
  prove either receives only the test split. The trainer fixture ignores its rows.
- **Ghost-box quote-validation control:** the sole summary case expects TaskError,
  so it cannot distinguish quote validation from rejecting every payload.
- **Ghost-box date/coverage tests:** both downloaded rows fit the queried range,
  and the coverage-query range equals the downloaded range. Those fixtures do not
  discriminate ignored date filtering or query-echoed coverage.
- **Missing interface details and research-runner outcomes:** exact behavior for
  tested schemas/errors should be declared; the local-executor decision did not
  match the v06 signature; the empty-suite case was not actually exercised.

## Direct counterexample execution

The following were rerun against the original v06 files, using pinned source
snapshots and the isolated Windows validation environment. Each mutation changes
application behavior without editing the original files.

| Original v06 suite | Unmodified result | Deliberately wrong implementation | Mutated result |
|---|---|---|---|
| ReflexModels | 16 passed | Always reports fallback_required=True | 16 passed |
| Llm-bender-lab | 7 passed | Passes all rows to trainer and both evaluations | 7 passed |
| Ghost-box core tests | 7 passed | checked_items always raises TaskError | 7 passed |

These surviving defects directly substantiate the review's three negative-control
findings. The v07 evidence separately demonstrates detection of the corresponding
wrong behaviors after correction. Logs and exact mutation sources are retained
under `app-core-v06/ai-review-v01/adjudication/`.

## Consequence for this demo

Retain the substantive corrections. Do not treat the word "new", historical paths,
or test organization alone as automatic rejection rules. Preserve the original AI
ratings and this adjudication separately. A complete second annotation round is
not required merely to correct these overstated explanations; acceptance for the
utility demo remains distinct from an independent reviewer approving every v07
record or from proving general test-generation quality.
