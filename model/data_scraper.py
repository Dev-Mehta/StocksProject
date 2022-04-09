from .model import StockScreener, StocksToCsv
import yfinance as yf
import pandas as pd
from datetime import timedelta, datetime
import time
df = pd.read_csv('nifty100.csv')
tickers = df.Symbol.values.tolist()
StocksToCsv(tickers).download()