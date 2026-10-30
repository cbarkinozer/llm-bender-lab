# ghost-box — assistant review

## Whole-app request

Make me a small Python desktop email assistant called Ghost-box that runs locally on my Mac. I want to connect one Gmail or Outlook account at a time, explicitly fetch messages for a date range, browse them, search the downloaded mail by text with sender and date filters, and select messages to summarize or ask questions about using a local model. Keep downloaded emails and derived results in RAM rather than an email database. Searches and answers must make the local coverage clear; finding nothing in downloaded mail must not claim that no such email exists anywhere. Summarization should receive only the selected messages and answers should retain references to their source messages. Keep the window responsive during fetches and generation, show progress and useful errors, and let me cancel work. Let me choose a local MLX or GGUF model, reuse it for follow-ups, unload it manually or after five idle minutes, and clear downloaded mail and derived results explicitly. Changing accounts must not mix the old account's mail into the new one. No background synchronization or automatic sending is needed. Give me a practical single-window app with setup and run instructions, not just isolated functions.

## Decisions and corrections

- Keep one active account and RAM-only email data. Search can only make claims about explicitly downloaded mail.
- Literal filtering is case-insensitive with Turkish-aware folding; ranked search is a separate operation.
- Choose local-time UI date ranges with timezone/DST conversion; document boundaries before adding date assertions.

## Important limits / missing acceptance checks

- Core store/search/evidence tests do not yet cover provider fetching, date filter integration, cancellation races, history cleanup or model lifecycle.
- GUI responsiveness and model-generated summary factuality need separate review.

## Requirement-to-test review

### R1 — Fetch only on request for the active account and selected range.

**Core check:** Fake provider receives the requested account/range; duplicate IDs do not create duplicate displayed messages; initial read makes no provider call.

**Current coverage:** partial. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R2 — Search respects downloaded scope and combined filters.

**Core check:** Fixture mail outside the selected sender/date range is excluded even when text matches; an empty result retains coverage metadata rather than an existence claim.

**Current coverage:** partial. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R3 — Selected-message inference retains provenance.

**Core check:** Fake summarizer receives only selected IDs/content; citations identify allowed source IDs; empty selection does not launch unrelated inbox inference.

**Current coverage:** partial. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R4 — Cancellation does not apply stale results.

**Core check:** Cancel operation A, start B, then deliver a delayed callback from A; callback; stored/displayed result still belongs to B and operation state is settled.

**Current coverage:** gap. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R5 — Account changes and clear remove old in-memory mail and derived results.

**Core check:** Populate account A and its results, clear/switch, then assert no A IDs/results remain accessible through application operations.

**Current coverage:** partial. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R6 — Reuse and unload local model according to explicit lifecycle.

**Core check:** With a fake worker/clock, two requests reuse one load; at the agreed five-minute idle boundary the worker unloads; explicit unload releases it.

**Current coverage:** gap. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

## Core tests included

- `tests/test_core.py::test_session_mail_is_not_restored_and_accounts_do_not_mix`
- `tests/test_core.py::test_clear_removes_mail_and_coverage`
- `tests/test_core.py::test_search_respects_the_explicit_downloaded_scope`
- `tests/test_core.py::test_literal_sender_filter_is_unicode_aware`
- `tests/test_core.py::test_long_mail_splitting_preserves_exact_unicode_content`
- `tests/test_core.py::test_task_cap_does_not_silently_discard_selected_content`
- `tests/test_core.py::test_summary_quote_cannot_be_borrowed_from_another_email`

## Manual checks

- Native window responsiveness, selection behavior, sign-in flows and accessible layout.
- Summary factuality on representative messages and citations; a fake model cannot certify semantic accuracy.
- Verify no mail-content persistence using controlled storage observation, beyond isolated core tests.
