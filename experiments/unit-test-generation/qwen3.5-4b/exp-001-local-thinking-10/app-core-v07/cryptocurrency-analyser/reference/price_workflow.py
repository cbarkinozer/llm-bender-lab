"""New reference orchestration boundary over real pandas calculations."""
from datetime import date
import pandas as pd
from coin_comparator import calculate_cumulative_returns, calculate_correlation

def analyze(tickers, start, end, *, provider=None, csv_path=None):
    if not tickers or date.fromisoformat(start)>=date.fromisoformat(end): raise ValueError('Invalid selection')
    symbols=[t.upper() if t.upper().endswith('-USD') else t.upper()+'-USD' for t in tickers]
    if csv_path is not None:
        prices=pd.read_csv(csv_path,index_col=0,parse_dates=True); source='csv'
    else:
        if provider is None: raise ValueError('Provider or saved CSV required')
        prices=provider(symbols,start,end).copy(deep=True); source='provider'
    prices=prices.reindex(columns=symbols).loc[lambda frame:(frame.index>=start)&(frame.index<end)]
    omitted=[symbol for symbol in symbols if prices[symbol].isna().all()]
    prices=prices.dropna(axis=1,how='all')
    if prices.empty: raise ValueError('No usable price observations')
    first=prices.apply(lambda column:column.dropna().iloc[0])
    if (first<=0).any(): raise ValueError('Invalid first-observed baseline')
    return {'returns':calculate_cumulative_returns(prices),'correlation':calculate_correlation(prices),'omitted':omitted,
            'source':source,'observed_start':prices.index.min().date().isoformat(),
            'observed_end':prices.index.max().date().isoformat()}
