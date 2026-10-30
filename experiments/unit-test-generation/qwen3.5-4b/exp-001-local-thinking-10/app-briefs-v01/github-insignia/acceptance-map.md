# GitHub-insignia — draft core acceptance map

Reproduce the usable dashboard MVP, not all defensive regression cases as separate output tests.

These are proposed checks, not an executed suite or proof of complete coverage.

| ID | Observable requirement | Concrete oracle / core check | Level |
|---|---|---|---|
| R1 | Use the declared repository scope and byte-based language shares. | Owned repos with stars 5 and 9, a fork with 100 and a foreign repo with 300 produce 14 stars and 2 repos; language bytes 500 Rust/300 Python produce 62.5%/37.5%. | unit |
| R2 | Offer deterministic repository sorting. | Stars ties resolve alphabetically; activity uses push timestamp, not repository metadata update time; absent push dates sort last. | unit |
| R3 | Use rolling twelve-calendar-month UTC activity and disclose unavailable data. | At fixed leap-day/timezone inputs assert exact window boundaries; no token gives activity=None, while authenticated zero contributions remains 0. | unit/integration |
| R4 | Fetch complete paginated data through official APIs. | A two-page fixture contributes both pages exactly once; no language requests for excluded repositories; GraphQL errors cannot become successful empty activity. | integration |
| R5 | Only explicit refresh replaces durable state. | Cold read makes zero upstream calls; refresh survives restart; HTTP, GraphQL or write failure preserves identical old snapshot bytes/time; malformed nested cache is rejected. | integration |
| R6 | Web and MCP expose one consistent snapshot without credentials. | Refresh via one interface, read through the other, compare actual values; fixture token absent from responses, cache and sanitized errors. | integration |

## Public test boundary (proposal)

HTTP endpoints plus three MCP tools; injectable GitHub transport and clock. Internal file/function structure remains free.

## Decisions still needing agreement

- Confirm the existing agreed scope and UTC window still match this compact reproduction.

## Manual / live checks

- Desktop/mobile layout, readability, keyboard interaction and screenshot appearance.
- One live authenticated contribution fetch; fixture success alone does not prove live API compatibility.

## Candidate existing evidence — not automatically selected

- `tests/test_requirements.py`
- `tests/test_revisions.py`
- `tests/conftest.py`

Source revision: `b44bd4ae59aa2d88d2334b1ae1a3c75089f3d07d`. These prompts are reconstructed drafts, not historical original user messages. Split role is unassigned; never use the same app/scenario for both SFT and claimed held-out improvement.
