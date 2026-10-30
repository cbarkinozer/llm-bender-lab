# cryptocurrency-analyser — draft core acceptance map

Explicitly narrowed whole usable research app, not a reproduction of the historical full crypto automation repository. Existing tests only partially cover this requested app.

These are proposed checks, not an executed suite or proof of complete coverage.

| ID | Observable requirement | Concrete oracle / core check | Level |
|---|---|---|---|
| R1 | Use the selected tickers/date range and distinguish provider failure. | Fake provider receives normalized BTC-USD/date range; transport error appears as failure, not a successful empty chart. | integration |
| R2 | Compute cumulative rather than daily returns. | Prices [100,150,75] yield [0,0.5,-0.25]; second series [20,10,30] yields [0,-0.5,0.5]; original data unchanged. | unit |
| R3 | Preserve partial missingness and omit all-missing series. | One NaN inside a valid coin remains missing; an entirely NaN coin is excluded; absent values are not replaced with zero prices. | unit/integration |
| R4 | Compute and visualize correct correlations and returns. | Oppositely moving nonconstant price series give -1 correlation; plotted named return series contain the exact expected values. | unit/integration |
| R5 | Support deterministic offline data with honest metadata. | Load a tiny saved CSV, derive the same calculations as the corresponding fake-provider response and label source/time accurately. | integration |
| R6 | Reject or explicitly report unusable input. | Empty ticker/date-range and zero/missing first baseline follow the owner-approved error policy rather than silently yielding misleading finite metrics. | unit/integration |

## Public test boundary (proposal)

Public price-analysis request/response plus fetch and render adapters; numeric calculations remain real, external download mocked.

## Decisions still needing agreement

- Approve this price-research MVP scope; the source repo also contains unrelated influencer/LLM/posting workflows.
- Agree first-missing/zero baseline policy, timezone/date inclusivity and offline file schema.

## Manual / live checks

- Browser chart readability, data-source attribution and a live provider check.

## Candidate existing evidence — not automatically selected

- `tests/test_coin_comparator.py`

Source revision: `cdefa3681b17a3f24980158e2edc66e8cbc353f2`. These prompts are reconstructed drafts, not historical original user messages. Split role is unassigned; never use the same app/scenario for both SFT and claimed held-out improvement.
