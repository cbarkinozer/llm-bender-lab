import pandas as pd
from pandas.testing import assert_frame_equal
from coin_comparator import fetch_data


def test_fetch_drops_only_entirely_missing_tickers(monkeypatch):
    from unittest.mock import Mock
    prices = pd.DataFrame({'BTC-USD': [10., 12.], 'ETH-USD': [float('nan'), 3.], 'MISSING-USD': [float('nan'), float('nan')]})
    download = Mock(return_value={'Adj Close': prices})
    result = fetch_data(['BTC-USD', 'ETH-USD', 'MISSING-USD'], '2026-01-01 00:00:00', '2026-01-03 00:00:00', download=download)
    assert_frame_equal(result, pd.DataFrame({'BTC-USD': [10., 12.], 'ETH-USD': [float('nan'), 3.]}))
    from datetime import datetime
    download.assert_called_once_with(['BTC-USD', 'ETH-USD', 'MISSING-USD'], start=datetime(2026, 1, 1), end=datetime(2026, 1, 3), auto_adjust=False)
