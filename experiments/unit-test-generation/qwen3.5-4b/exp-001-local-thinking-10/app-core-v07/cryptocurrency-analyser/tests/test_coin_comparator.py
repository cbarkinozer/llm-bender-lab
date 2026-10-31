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


