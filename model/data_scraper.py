from . import model as md
import yfinance as yf
import pandas as pd
from datetime import timedelta, datetime

df = pd.read_csv('nifty100.csv')
tickers = df.Symbol.values.tolist()
big_data = pd.DataFrame()
for ticker in tickers:
	model = md.StockClassifier(ticker=ticker)
	result, df = model.train()
	big_data['{}'.format(ticker)] = df
	
	print('Done for {}'.format(ticker))
big_data.to_csv('backtest_results.csv')