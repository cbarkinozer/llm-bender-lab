import pandas as pd
from pandas.testing import assert_frame_equal
from coin_comparator import calculate_cumulative_returns


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


import pytest


def test_first_observed_price_is_selected_independently_per_series():
    missing=float('nan')
    prices=pd.DataFrame({'late':[missing,10.,20.], 'early':[2.,4.,missing], 'missing':[missing,missing,missing]})
    expected=pd.DataFrame({'late':[missing,0.,1.], 'early':[0.,1.,missing], 'missing':[missing,missing,missing]})
    assert_frame_equal(calculate_cumulative_returns(prices),expected)


@pytest.mark.parametrize('baseline',[0.,-1.])
def test_nonpositive_observed_baselines_are_rejected(baseline):
    with pytest.raises(ValueError,match='baseline'):
        calculate_cumulative_returns(pd.DataFrame({'coin':[baseline,10.]}))
