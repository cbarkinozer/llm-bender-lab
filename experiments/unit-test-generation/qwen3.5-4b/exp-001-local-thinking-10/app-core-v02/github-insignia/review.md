# GitHub-insignia — assistant review

## Whole-app request

Build me a local GitHub dashboard in Python with FastAPI and FastMCP for cbarkinozer. I want to start it on my Mac, open it in a browser, refresh when I choose, take screenshots and close it without hosting or paying for a service. Show my profile, received stars, repository count, languages, best repositories sorted by stars or recent code pushes, and contributions, commits, opened PRs and opened issues over the last twelve calendar months in UTC, including a daily calendar. Repository and language statistics should use my public owned repositories, excluding forks but including archived ones; calculate languages from GitHub language bytes. Explain the scope of each number, and don't turn unavailable information into zero. Use official GitHub APIs and an optional server-side token; without a token, show public data and mark contribution data unavailable. Cache the last successful complete snapshot across restarts, never fetch just because I opened the page, and preserve the old snapshot and timestamp if refresh fails. Expose refresh, activity summary and top repositories through MCP using the same data as the dashboard. Keep credentials out of outputs and saved snapshots. Make the interface clean and usable on desktop and phone widths, and include simple startup instructions; no letter grade is needed.

## Decisions and corrections

- Keep existing agreed public-owned/nonfork scope and twelve-calendar-month UTC window.
- Keep private/token-visible contribution scope separate from public repository statistics.
- No grade; no live data required in core tests.

## Important limits / missing acceptance checks

- Browser appearance and real authenticated GitHub compatibility are manual/live checks.

## Requirement-to-test review

### R1 — Use the declared repository scope and byte-based language shares.

**Core check:** Owned repos with stars 5 and 9, a fork with 100 and a foreign repo with 300 produce 14 stars and 2 repos; language bytes 500 Rust/300 Python produce 62.5%/37.5%.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R2 — Offer deterministic repository sorting.

**Core check:** Stars ties resolve alphabetically; activity uses push timestamp, not repository metadata update time; absent push dates sort last.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R3 — Use rolling twelve-calendar-month UTC activity and disclose unavailable data.

**Core check:** At fixed leap-day/timezone inputs assert exact window boundaries; no token gives activity=None, while authenticated zero contributions remains 0.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R4 — Fetch complete paginated data through official APIs.

**Core check:** A two-page fixture contributes both pages exactly once; no language requests for excluded repositories; GraphQL errors cannot become successful empty activity.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R5 — Only explicit refresh replaces durable state.

**Core check:** Cold read makes zero upstream calls; refresh survives restart; HTTP, GraphQL or write failure preserves identical old snapshot bytes/time; malformed nested cache is rejected.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R6 — Web and MCP expose one consistent snapshot without credentials.

**Core check:** Refresh via one interface, read through the other, compare actual values; fixture token absent from responses, cache and sanitized errors.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

## Core tests included

- `tests/test_requirements.py::test_r1_filter_calculation_and_byte_shares`
- `tests/test_requirements.py::test_r1_empty_language_data_is_not_a_fabricated_percentage`
- `tests/test_requirements.py::test_r2_sort_stars_activity_ties_and_invalid_sort`
- `tests/test_requirements.py::test_r3_utc_leap_date_and_year_splitting`
- `tests/test_requirements.py::test_r4_pagination_and_filter_before_language_requests`
- `tests/test_requirements.py::test_r5_graphql_window_combination_and_secret_absence`
- `tests/test_requirements.py::test_r6_cache_read_restart_and_manual_refresh`
- `tests/test_requirements.py::test_r7_failed_refresh_preserves_complete_snapshot`
- `tests/test_requirements.py::test_r7_graphql_errors_and_timeout_are_failures`
- `tests/test_requirements.py::test_r8_cache_write_failure_preserves_memory_and_disk`
- `tests/test_requirements.py::test_r9_fastapi_and_mcp_share_service`
- `tests/test_revisions.py::test_actual_transport_timeout_is_sanitized`
- `tests/test_revisions.py::test_graphql_http_200_errors_preserve_previous_snapshot`
- `tests/test_revisions.py::test_real_zero_activity_stays_zero`
- `tests/test_revisions.py::test_pagination_cannot_forward_credentials_to_another_host`
- `tests/test_revisions.py::test_corrupt_cache_is_unavailable`
- `tests/test_revisions.py::test_missing_graphql_totals_does_not_turn_into_zero`
- `tests/test_revisions.py::test_http_mcp_transport_and_refresh_tool`
- `tests/test_revisions.py::test_structurally_invalid_cache_is_rejected`
- `tests/test_revisions.py::test_authenticated_snapshot_survives_restart`

## Manual checks

- Desktop/mobile layout, readability, keyboard interaction and screenshot appearance.
- One live authenticated contribution fetch; fixture success alone does not prove live API compatibility.
