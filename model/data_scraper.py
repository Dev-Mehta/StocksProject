from .model import StockScreener
import yfinance as yf
import pandas as pd
from datetime import timedelta, datetime
import time
df = pd.read_csv('nifty100.csv')
tickers = df.Symbol.values.tolist()
start = time.time()
for ticker in tickers:
	model = StockScreener(ticker=ticker)
	result = model.train()
	print('Done for {}'.format(ticker))
	if result['buy_call']:
		print(f"Buy call found in {ticker}")
print(time.time() - start)