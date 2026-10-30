# ghost-box — draft core acceptance map

Core whole email-assistant MVP; automatic sending, packaging and complete provider/backend support matrices are excluded explicitly.

These are proposed checks, not an executed suite or proof of complete coverage.

| ID | Observable requirement | Concrete oracle / core check | Level |
|---|---|---|---|
| R1 | Fetch only on request for the active account and selected range. | Fake provider receives the requested account/range; duplicate IDs do not create duplicate displayed messages; initial read makes no provider call. | integration |
| R2 | Search respects downloaded scope and combined filters. | Fixture mail outside the selected sender/date range is excluded even when text matches; an empty result retains coverage metadata rather than an existence claim. | unit/integration |
| R3 | Selected-message inference retains provenance. | Fake summarizer receives only selected IDs/content; citations identify allowed source IDs; empty selection does not launch unrelated inbox inference. | integration |
| R4 | Cancellation does not apply stale results. | Cancel operation A, start B, then deliver a delayed callback from A; callback; stored/displayed result still belongs to B and operation state is settled. | integration |
| R5 | Account changes and clear remove old in-memory mail and derived results. | Populate account A and its results, clear/switch, then assert no A IDs/results remain accessible through application operations. | integration |
| R6 | Reuse and unload local model according to explicit lifecycle. | With a fake worker/clock, two requests reuse one load; at the agreed five-minute idle boundary the worker unloads; explicit unload releases it. | unit/integration |

## Public test boundary (proposal)

Application operations for fetch/search/select/infer/cancel/clear plus fake providers/model worker and an injectable clock; Qt adapter checks separate.

## Decisions still needing agreement

- Agree exact sender/text matching and inclusive/exclusive date-range boundaries.
- Agree whether cancelling leaves partial output visible and when the five-minute timer resets.

## Manual / live checks

- Native window responsiveness, selection behavior, sign-in flows and accessible layout.
- Summary factuality on representative messages and citations; a fake model cannot certify semantic accuracy.
- Verify no mail-content persistence using controlled storage observation, beyond isolated core tests.

## Candidate existing evidence — not automatically selected

- `tests/test_fetch.py`
- `tests/test_search.py`
- `tests/test_mail_controls.py`
- `tests/test_summary.py`
- `tests/test_worker.py`
- `tests/test_model_session.py`

Source revision: `fc0fd7dbb824b9d33cd695ac68d0d79320eb7faa`. These prompts are reconstructed drafts, not historical original user messages. Split role is unassigned; never use the same app/scenario for both SFT and claimed held-out improvement.
