# cryptocurrency-analyser — assistant review

## Whole-app request

Build me a small local Python cryptocurrency research app where I can choose coin tickers and a date range, fetch historical prices, compare their cumulative returns and correlations, and view charts and a concise data summary in a browser. Start with a working price-comparison workflow rather than every possible trading indicator or a trading bot. Calculate returns relative to the first observed price for each series, preserve missing observations instead of inventing prices, omit a coin only when its whole series is missing, and label the data source, timestamps and unavailable results clearly. Let me also run it with a saved sample dataset when offline. A provider failure should show a useful error rather than fabricated zero returns, and malformed selections or unusable baselines should be explained. Keep fetching, calculations and visualization separate enough to test with deterministic fixtures, never place trades or publish posts, and make the web workflow and setup straightforward on my Mac without paid services.

## Decisions and corrections

- Use a clearly named price-comparison MVP; remove influencer scraping, LLM recommendations, posting and trading from this demo request.
- Return = current/first-row price - 1; preserve interior NaNs, remove only all-missing columns.
- Zero/missing baseline and invalid inputs remain unresolved behavior gaps, not license to assert fabricated finite returns.

## Important limits / missing acceptance checks

- CSV/offline app workflow and validation/error presentation are not yet represented by the comparator module.
- Current tests verify numeric/plot/orchestration core; provider error propagation and missing baselines need additional acceptance work.

## Requirement-to-test review

### R1 — Use the selected tickers/date range and distinguish provider failure.

**Core check:** Fake provider receives normalized BTC-USD/date range; transport error appears as failure, not a successful empty chart.

**Current coverage:** partial. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R2 — Compute cumulative rather than daily returns.

**Core check:** Prices [100,150,75] yield [0,0.5,-0.25]; second series [20,10,30] yields [0,-0.5,0.5]; original data unchanged.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R3 — Preserve partial missingness and omit all-missing series.

**Core check:** One NaN inside a valid coin remains missing; an entirely NaN coin is excluded; absent values are not replaced with zero prices.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R4 — Compute and visualize correct correlations and returns.

**Core check:** Oppositely moving nonconstant price series give -1 correlation; plotted named return series contain the exact expected values.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R5 — Support deterministic offline data with honest metadata.

**Core check:** Load a tiny saved CSV, derive the same calculations as the corresponding fake-provider response and label source/time accurately.

**Current coverage:** gap. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R6 — Reject or explicitly report unusable input.

**Core check:** Empty ticker/date-range and zero/missing first baseline follow the owner-approved error policy rather than silently yielding misleading finite metrics.

**Current coverage:** gap. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

## Core tests included

- `tests/test_coin_comparator.py::test_returns_are_relative_to_first_price_not_daily_changes`
- `tests/test_coin_comparator.py::test_returns_preserve_dates_and_input_prices`
- `tests/test_coin_comparator.py::test_missing_price_remains_missing`
- `tests/test_coin_comparator.py::test_correlation_detects_opposite_price_movements`
- `tests/test_coin_comparator.py::test_fetch_drops_only_entirely_missing_tickers`
- `tests/test_coin_comparator.py::test_combined_plot_contains_correlation_and_each_return_series`
- `tests/test_coin_comparator.py::test_comparator_normalizes_tickers_and_passes_dates_to_fetch`

## Manual checks

- Browser chart readability, data-source attribution and a live provider check.
