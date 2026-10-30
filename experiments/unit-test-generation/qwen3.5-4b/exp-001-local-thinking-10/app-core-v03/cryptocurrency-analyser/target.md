## Decisions and unresolved questions

These are assistant-proposed design choices for this demo, not recorded human answers.

- Use a clearly named price-comparison MVP; remove influencer scraping, LLM recommendations, posting and trading from this demo request.
- Return = current/first-row price - 1; preserve interior NaNs, remove only all-missing columns.

Unresolved/nonessential choices:
- Live-provider UI retry/backoff behavior remains open.

## Proposed interface agreement

Proposed numeric compatibility module `coin_comparator` and new public `price_workflow.analyze`:
- `calculate_cumulative_returns(prices:DataFrame)` -> same-index/column DataFrame current/first-row - 1. Never mutate input, preserve interior NaNs. `_calculate_correlation(prices)` -> full Pearson price-correlation DataFrame, exact column/index order. `_fetch_data(tickers,start_date,end_date)` accepts timestamp strings YYYY-MM-DD HH:MM:SS, delegates yf.download(tickers,start=datetime,end=datetime), selects Adj Close and drops only entirely missing columns. These legacy underscore functions are explicitly declared compatibility seams; new apps may expose public aliases.
- `_plot_combined(correlation,prices,tickers)` -> Plotly figure with heatmap then named cumulative-return scatter per ticker. `coin_comparator(tickers,start,end)` normalizes to uppercase -USD, adds midnight time strings, calls fetch and pio.to_html(full_html=True), returns HTML. yf.download/_fetch_data/pio.to_html are explicitly declared I/O seams for offline tests.
- `price_workflow.analyze(tickers,start,end,provider=None,csv_path=None)` -> `{returns:DataFrame,correlation:DataFrame,source:"csv"|"provider",observed_start:YYYY-MM-DD,observed_end:YYYY-MM-DD}`. Tickers normalize uppercase -USD. Date range [start,end); provider(normalized_tickers,start,end) returns price DataFrame. CSV uses Date index and named ticker columns; no fetch in CSV mode. Saved/provider routes produce identical dates and numeric values; pandas inferred freq metadata is not part of the contract.
- Empty tickers or reversed dates raise ValueError before fetch. Drop all-missing series; zero/NaN first-row baseline raises ValueError mentioning baseline. This explicitly selects rejection rather than inventing/forward-filling a baseline. Provider RuntimeError propagates for UI to display, never fabricate zeros. Actual browser chart/metadata/error display needs a manual check.
Dependencies: Python, pytest, pandas, Plotly, yfinance for compatibility code; tests never call live services.

Declared application import inventory (checked against test AST):
- `coin_comparator` (module)
- `coin_comparator._calculate_correlation`
- `coin_comparator._fetch_data`
- `coin_comparator._plot_combined`
- `coin_comparator.calculate_cumulative_returns`
- `price_workflow.analyze`

## Requirement-to-test map

R1: Use the selected tickers/date range and distinguish provider failure.
- `tests/test_coin_comparator.py::test_fetch_drops_only_entirely_missing_tickers`
- `tests/test_coin_comparator.py::test_comparator_normalizes_tickers_and_passes_dates_to_fetch`
- `tests/test_workflow.py::test_saved_csv_matches_provider_calculation_and_declares_source`
- `tests/test_workflow.py::test_provider_failure_does_not_produce_zero_returns`

R2: Compute cumulative rather than daily returns.
- `tests/test_coin_comparator.py::test_returns_are_relative_to_first_price_not_daily_changes`
- `tests/test_coin_comparator.py::test_returns_preserve_dates_and_input_prices`
- `tests/test_workflow.py::test_saved_csv_matches_provider_calculation_and_declares_source`

R3: Preserve partial missingness and omit all-missing series.
- `tests/test_coin_comparator.py::test_missing_price_remains_missing`
- `tests/test_coin_comparator.py::test_fetch_drops_only_entirely_missing_tickers`

R4: Compute and visualize correct correlations and returns.
- `tests/test_coin_comparator.py::test_correlation_detects_opposite_price_movements`
- `tests/test_coin_comparator.py::test_combined_plot_contains_correlation_and_each_return_series`
- `tests/test_coin_comparator.py::test_comparator_normalizes_tickers_and_passes_dates_to_fetch`

R5: Support deterministic offline data with honest metadata.
- `tests/test_workflow.py::test_saved_csv_matches_provider_calculation_and_declares_source`

R6: Reject or explicitly report unusable input.
- `tests/test_workflow.py::test_provider_failure_does_not_produce_zero_returns`
- `tests/test_workflow.py::test_bad_selection_fails_before_fetch`
- `tests/test_workflow.py::test_unusable_first_row_is_reported_not_filled`

R7: Usable delivery, documented commands and the declared live/manual integration checks.

Manual/live: M1, M2

## Complete test files

File: tests/test_coin_comparator.py
```python
"""Deterministic numeric oracles; data downloads are replaced at the I/O boundary."""
import sys
from pathlib import Path
import pandas as pd
from pandas.testing import assert_frame_equal

from coin_comparator import _calculate_correlation, _fetch_data, calculate_cumulative_returns


def test_returns_are_relative_to_first_price_not_daily_changes():
    prices = pd.DataFrame({'BTC': [100., 150., 75.], 'ETH': [20., 10., 30.]})
    expected = pd.DataFrame({'BTC': [0., .5, -.25], 'ETH': [0., -.5, .5]})
    assert_frame_equal(calculate_cumulative_returns(prices), expected)


def test_returns_preserve_dates_and_input_prices():
    dates = pd.date_range('2026-01-01', periods=2)
    prices = pd.DataFrame({'BTC': [10., 15.]}, index=dates)
    original = prices.copy(deep=True)
    result = calculate_cumulative_returns(prices)
    assert_frame_equal(prices, original)
    assert_frame_equal(result, pd.DataFrame({'BTC': [0., .5]}, index=dates))


def test_missing_price_remains_missing():
    prices = pd.DataFrame({'BTC': [100., float('nan'), 200.]})
    expected = pd.DataFrame({'BTC': [0., float('nan'), 1.]})
    assert_frame_equal(calculate_cumulative_returns(prices), expected)


def test_correlation_detects_opposite_price_movements():
    prices = pd.DataFrame({'up': [1., 2., 3.], 'down': [6., 4., 2.]})
    expected = pd.DataFrame([[1., -1.], [-1., 1.]], index=['up', 'down'], columns=['up', 'down'])
    assert_frame_equal(_calculate_correlation(prices), expected)


def test_fetch_drops_only_entirely_missing_tickers(monkeypatch):
    from unittest.mock import Mock
    prices = pd.DataFrame({'BTC-USD': [10., 12.], 'ETH-USD': [float('nan'), 3.], 'MISSING-USD': [float('nan'), float('nan')]})
    download = Mock(return_value={'Adj Close': prices})
    monkeypatch.setattr('coin_comparator.yf.download', download)
    result = _fetch_data(['BTC-USD', 'ETH-USD', 'MISSING-USD'], '2026-01-01 00:00:00', '2026-01-03 00:00:00')
    assert_frame_equal(result, pd.DataFrame({'BTC-USD': [10., 12.], 'ETH-USD': [float('nan'), 3.]}))
    from datetime import datetime
    download.assert_called_once_with(['BTC-USD', 'ETH-USD', 'MISSING-USD'], start=datetime(2026, 1, 1), end=datetime(2026, 1, 3))


def test_combined_plot_contains_correlation_and_each_return_series():
    from coin_comparator import _plot_combined
    prices = pd.DataFrame({'BTC': [10., 15.], 'ETH': [20., 10.]}, index=pd.date_range('2026-01-01', periods=2))
    correlation = pd.DataFrame([[1., -1.], [-1., 1.]], index=['BTC', 'ETH'], columns=['BTC', 'ETH'])
    figure = _plot_combined(correlation, prices, ['BTC', 'ETH'])
    assert [trace.type for trace in figure.data] == ['heatmap', 'scatter', 'scatter']
    assert list(figure.data[1].y) == [0., .5]
    assert list(figure.data[2].y) == [0., -.5]
    assert [trace.name for trace in figure.data[1:]] == ['BTC', 'ETH']


def test_comparator_normalizes_tickers_and_passes_dates_to_fetch(monkeypatch):
    from unittest.mock import Mock
    import coin_comparator as module
    prices = pd.DataFrame({'BTC-USD': [10., 15.]})
    fetch = Mock(return_value=prices)
    render = Mock(return_value='<html>fixture chart</html>')
    monkeypatch.setattr(module, '_fetch_data', fetch)
    monkeypatch.setattr(module.pio, 'to_html', render)
    assert module.coin_comparator(['btc'], '2026-01-01', '2026-01-02') == '<html>fixture chart</html>'
    fetch.assert_called_once_with(['BTC-USD'], start_date='2026-01-01 00:00:00', end_date='2026-01-02 00:00:00')
    assert render.call_args.kwargs == {'full_html': True}
```

File: tests/test_workflow.py
```python
"""Proposed application operation tests saved data, failures and validation."""
from unittest.mock import Mock
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest


def prices():
    return pd.DataFrame({'BTC-USD':[100.,150.,75.], 'ETH-USD':[20.,10.,30.]},
                        index=pd.date_range('2026-01-01', periods=3, name='Date'))


def test_saved_csv_matches_provider_calculation_and_declares_source(tmp_path):
    from price_workflow import analyze
    path = tmp_path/'prices.csv'
    prices().to_csv(path)
    provider = Mock(return_value=prices())
    live = analyze(['btc','eth'], '2026-01-01','2026-01-04', provider=provider)
    offline = analyze(['btc','eth'], '2026-01-01','2026-01-04', csv_path=path)
    provider.assert_called_once_with(['BTC-USD','ETH-USD'], '2026-01-01','2026-01-04')
    assert_frame_equal(live['returns'], offline['returns'], check_freq=False)
    assert offline['returns']['BTC-USD'].tolist() == [0.,.5,-.25]
    assert offline['source'] == 'csv'
    assert offline['observed_start'] == '2026-01-01'
    assert offline['observed_end'] == '2026-01-03'


def test_provider_failure_does_not_produce_zero_returns():
    from price_workflow import analyze
    with pytest.raises(RuntimeError, match='provider unavailable'):
        analyze(['btc'], '2026-01-01','2026-01-04', provider=Mock(side_effect=RuntimeError('provider unavailable')))


@pytest.mark.parametrize('tickers,start,end', [([], '2026-01-01','2026-01-04'),
    (['btc'], '2026-01-04','2026-01-01')])
def test_bad_selection_fails_before_fetch(tickers,start,end):
    from price_workflow import analyze
    provider = Mock()
    with pytest.raises(ValueError):
        analyze(tickers,start,end,provider=provider)
    provider.assert_not_called()


@pytest.mark.parametrize('baseline', [0.,float('nan')])
def test_unusable_first_row_is_reported_not_filled(baseline):
    from price_workflow import analyze
    frame = prices()
    frame.loc[frame.index[0], 'BTC-USD'] = baseline
    with pytest.raises(ValueError, match='baseline'):
        analyze(['btc','eth'], '2026-01-01','2026-01-04',provider=Mock(return_value=frame))
```

## Manual checks

M1: Browser chart readability, data-source attribution and a live provider check.
M2: Check actual browser sample-data option, data source/time labels and visible provider/baseline errors; the new reference API is not yet wired to the historical web UI.
