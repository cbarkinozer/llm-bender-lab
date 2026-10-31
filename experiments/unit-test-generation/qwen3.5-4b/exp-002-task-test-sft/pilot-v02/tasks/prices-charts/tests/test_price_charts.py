import pandas as pd
from pandas.testing import assert_frame_equal
from coin_comparator import calculate_correlation


def test_correlation_detects_opposite_price_movements():
    prices = pd.DataFrame({'up': [1., 2., 3.], 'down': [6., 4., 2.]})
    expected = pd.DataFrame([[1., -1.], [-1., 1.]], index=['up', 'down'], columns=['up', 'down'])
    assert_frame_equal(calculate_correlation(prices), expected)


def test_combined_plot_contains_correlation_and_each_return_series():
    from coin_comparator import plot_combined
    prices = pd.DataFrame({'BTC': [10., 15.], 'ETH': [20., 10.]}, index=pd.date_range('2026-01-01', periods=2))
    correlation = pd.DataFrame([[1., -1.], [-1., 1.]], index=['BTC', 'ETH'], columns=['BTC', 'ETH'])
    figure = plot_combined(correlation, prices, ['BTC', 'ETH'])
    assert [trace.type for trace in figure.data] == ['heatmap', 'scatter', 'scatter']
    assert list(figure.data[1].y) == [0., .5]
    assert list(figure.data[2].y) == [0., -.5]
    assert [trace.name for trace in figure.data[1:]] == ['BTC', 'ETH']


def test_plot_three_observations_uses_cumulative_not_daily_returns():
    from coin_comparator import plot_combined
    prices=pd.DataFrame({'BTC':[100.,150.,75.]})
    figure=plot_combined(prices.corr(),prices,['BTC'])
    assert list(figure.data[1].y) == [0.,.5,-.25]
