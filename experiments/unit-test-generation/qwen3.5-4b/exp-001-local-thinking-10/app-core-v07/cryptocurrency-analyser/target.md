## Decisions and unresolved questions

Proposed decisions:

- Use cumulative return=current/first-row price-1. Preserve interior missing values and omit all-missing series.
- Keep calculations separate from fetching and rendering; provide an offline CSV route.
- Use the first observed nonmissing price of each series; preserve leading/interior missing observations, reject nonpositive baselines and list all-missing tickers as omitted.

Unresolved/nonessential choices:
- Live-provider UI retry/backoff behavior remains open.

## Proposed interface agreement

Proposed public modules `coin_comparator` and `price_workflow`:
- calculate_cumulative_returns(prices:DataFrame) returns current/first-observed-nonmissing-price minus 1 per column. Preserve every missing observation, index, columns and input bytes/values. Nonpositive observed baselines raise ValueError mentioning baseline; an entirely missing column remains missing.
- calculate_correlation(prices) returns Pearson price correlation in input column order. plot_combined(correlation,prices,tickers) returns a Plotly heatmap followed by named cumulative-return scatter traces in ticker order.
- fetch_data(tickers,start,end,download=None) accepts timestamp strings YYYY-MM-DD HH:MM:SS; calls download(tickers,start=datetime,end=datetime,auto_adjust=False), reads Adj Close and drops only all-missing columns. download defaults to yf.download and is the public offline injection seam.
- analyze(tickers,start,end,provider=None,csv_path=None) returns {returns,correlation,omitted,source,observed_start,observed_end}. Normalize uppercase -USD ticker names; [start,end) date filtering; provider(symbols,start,end) returns a price DataFrame. CSV mode never calls provider. CSV/provider values and dates match, independent of pandas inferred frequency metadata. omitted lists requested all-missing/unavailable symbols in request order. source is csv or provider; observed bounds are ISO dates of the retained frame.
- Empty selection/reversed dates fail before fetching. No usable observations raises ValueError. Leading missing rows use the first later observed baseline; no forward fill. Nonpositive baseline raises ValueError mentioning baseline. Provider RuntimeError propagates without fabricated zero returns. Actual browser chart/error/source display remains manual.
Dependencies: Python, pytest, pandas, Plotly, yfinance; no live services in tests.

Public imports:
- `coin_comparator.calculate_correlation`
- `coin_comparator.calculate_cumulative_returns`
- `coin_comparator.fetch_data`
- `coin_comparator.plot_combined`
- `price_workflow.analyze`

## Requirement-to-test map

R1: Use the selected tickers/date range and distinguish provider failure.
- `tests/test_coin_comparator.py::test_fetch_drops_only_entirely_missing_tickers`
- `tests/test_workflow.py::test_saved_csv_matches_provider_calculation_and_declares_source`
- `tests/test_workflow.py::test_provider_failure_does_not_produce_zero_returns`

R2: Compute cumulative rather than daily returns.
- `tests/test_coin_comparator.py::test_returns_are_relative_to_first_price_not_daily_changes`
- `tests/test_coin_comparator.py::test_returns_preserve_dates_and_input_prices`
- `tests/test_workflow.py::test_saved_csv_matches_provider_calculation_and_declares_source`
- `tests/test_workflow.py::test_first_observed_baselines_and_omitted_series_are_reported`

R3: Preserve partial missingness and omit all-missing series.
- `tests/test_coin_comparator.py::test_missing_price_remains_missing`
- `tests/test_coin_comparator.py::test_fetch_drops_only_entirely_missing_tickers`
- `tests/test_workflow.py::test_first_observed_baselines_and_omitted_series_are_reported`

R4: Compute and visualize correct correlations and returns.
- `tests/test_coin_comparator.py::test_correlation_detects_opposite_price_movements`
- `tests/test_coin_comparator.py::test_combined_plot_contains_correlation_and_each_return_series`

R5: Support deterministic offline data with honest metadata.
- `tests/test_workflow.py::test_saved_csv_matches_provider_calculation_and_declares_source`

R6: Reject or explicitly report unusable input.
- `tests/test_workflow.py::test_provider_failure_does_not_produce_zero_returns`
- `tests/test_workflow.py::test_bad_selection_fails_before_fetch`
- `tests/test_workflow.py::test_unusable_first_row_is_reported_not_filled`
- `tests/test_workflow.py::test_first_observed_baselines_and_omitted_series_are_reported`

R7: Usable delivery, documented commands and the declared live/manual integration checks.

Manual/live: M1, M2

## Complete test files

File: tests/test_coin_comparator.py
```python
'Acceptance checks for observable application behavior.'
import pandas as pd
from pandas.testing import assert_frame_equal

from coin_comparator import calculate_correlation, fetch_data, calculate_cumulative_returns


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
    assert_frame_equal(calculate_correlation(prices), expected)


def test_fetch_drops_only_entirely_missing_tickers(monkeypatch):
    from unittest.mock import Mock
    prices = pd.DataFrame({'BTC-USD': [10., 12.], 'ETH-USD': [float('nan'), 3.], 'MISSING-USD': [float('nan'), float('nan')]})
    download = Mock(return_value={'Adj Close': prices})
    result = fetch_data(['BTC-USD', 'ETH-USD', 'MISSING-USD'], '2026-01-01 00:00:00', '2026-01-03 00:00:00', download=download)
    assert_frame_equal(result, pd.DataFrame({'BTC-USD': [10., 12.], 'ETH-USD': [float('nan'), 3.]}))
    from datetime import datetime
    download.assert_called_once_with(['BTC-USD', 'ETH-USD', 'MISSING-USD'], start=datetime(2026, 1, 1), end=datetime(2026, 1, 3), auto_adjust=False)


def test_combined_plot_contains_correlation_and_each_return_series():
    from coin_comparator import plot_combined
    prices = pd.DataFrame({'BTC': [10., 15.], 'ETH': [20., 10.]}, index=pd.date_range('2026-01-01', periods=2))
    correlation = pd.DataFrame([[1., -1.], [-1., 1.]], index=['BTC', 'ETH'], columns=['BTC', 'ETH'])
    figure = plot_combined(correlation, prices, ['BTC', 'ETH'])
    assert [trace.type for trace in figure.data] == ['heatmap', 'scatter', 'scatter']
    assert list(figure.data[1].y) == [0., .5]
    assert list(figure.data[2].y) == [0., -.5]
    assert [trace.name for trace in figure.data[1:]] == ['BTC', 'ETH']


```

File: tests/test_workflow.py
```python
'Acceptance checks for observable application behavior.'
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
    assert live['source'] == 'provider'
    assert offline['source'] == 'csv'
    assert_frame_equal(live['correlation'], prices().corr())
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


@pytest.mark.parametrize('baseline', [0.,-1.])
def test_unusable_first_row_is_reported_not_filled(baseline):
    from price_workflow import analyze
    frame = prices()
    frame.loc[frame.index[0], 'BTC-USD'] = baseline
    with pytest.raises(ValueError, match='baseline'):
        analyze(['btc','eth'], '2026-01-01','2026-01-04',provider=Mock(return_value=frame))

def test_first_observed_baselines_and_omitted_series_are_reported():
    from price_workflow import analyze
    frame=prices()
    frame.loc[frame.index[0],'BTC-USD']=float('nan')
    frame['MISSING-USD']=float('nan')
    result=analyze(['btc','eth','missing'],'2026-01-01','2026-01-04',provider=Mock(return_value=frame))
    expected=pd.DataFrame({'BTC-USD':[float('nan'),0.,-.5],'ETH-USD':[0.,-.5,.5]},index=frame.index)
    assert_frame_equal(result['returns'],expected)
    assert result['omitted'] == ['MISSING-USD']
    assert list(result['correlation'].columns) == ['BTC-USD','ETH-USD']

```

## Manual checks

M1: Check browser readability, chart data, source/time labels, offline sample selection and visible provider/baseline errors.
M2: Perform one live provider fetch using the documented setup.
