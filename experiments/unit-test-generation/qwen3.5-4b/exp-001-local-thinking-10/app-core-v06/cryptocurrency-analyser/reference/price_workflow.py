"""New reference orchestration boundary over real pandas calculations."""
from datetime import date
import pandas as pd
from coin_comparator import calculate_cumulative_returns, _calculate_correlation

def analyze(tickers, start, end, *, provider=None, csv_path=None):
    if not tickers or date.fromisoformat(start)>=date.fromisoformat(end): raise ValueError('Invalid selection')
    symbols=[t.upper() if t.upper().endswith('-USD') else t.upper()+'-USD' for t in tickers]
    if csv_path is not None:
        prices=pd.read_csv(csv_path,index_col=0,parse_dates=True); source='csv'
    else:
        if provider is None: raise ValueError('Provider or saved CSV required')
        prices=provider(symbols,start,end).copy(deep=True); source='provider'
    prices=prices.loc[(prices.index>=start)&(prices.index<end),symbols].dropna(axis=1,how='all')
    if prices.empty: raise ValueError('No usable price observations')
    first=prices.iloc[0]
    if first.isna().any() or (first<=0).any(): raise ValueError('Invalid first-row baseline')
    return {'returns':calculate_cumulative_returns(prices),'correlation':_calculate_correlation(prices),
            'source':source,'observed_start':prices.index.min().date().isoformat(),
            'observed_end':prices.index.max().date().isoformat()}
