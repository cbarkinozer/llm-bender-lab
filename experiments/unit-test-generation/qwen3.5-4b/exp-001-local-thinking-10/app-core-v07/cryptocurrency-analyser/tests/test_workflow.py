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

