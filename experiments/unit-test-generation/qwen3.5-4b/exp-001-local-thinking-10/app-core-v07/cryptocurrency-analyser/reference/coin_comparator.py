"""Authored public calculation/provider boundaries; no import-time fetching."""
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

def calculate_cumulative_returns(prices):
    baselines=prices.apply(lambda column:column.dropna().iloc[0] if column.notna().any() else float('nan'))
    if (baselines.dropna()<=0).any(): raise ValueError('Invalid baseline')
    return prices.div(baselines)-1

def calculate_correlation(prices): return prices.corr()

def fetch_data(tickers,start,end,*,download=None):
    download=download or yf.download
    return download(tickers,start=datetime.fromisoformat(start),end=datetime.fromisoformat(end),
                    auto_adjust=False)['Adj Close'].dropna(axis=1,how='all')

def plot_combined(correlation,prices,tickers):
    figure=make_subplots(rows=2,cols=1)
    figure.add_trace(go.Heatmap(z=correlation.values,x=correlation.columns,y=correlation.index),row=1,col=1)
    returns=calculate_cumulative_returns(prices)
    for ticker in tickers:
        if ticker in returns: figure.add_trace(go.Scatter(x=returns.index,y=returns[ticker],name=ticker),row=2,col=1)
    return figure
