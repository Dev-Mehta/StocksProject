import os, sys, django
sys.path.append("D:\Projects\StocksProject")
sys.path.append("D:\Projects\StockBlog")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stockmarket.settings")
django.setup()

from model.model import StockScreener
import pandas as pd
import time
df = pd.read_csv('nifty100.csv')
tickers = df.Symbol.values.tolist()
start = time.time()
buy_calls = []
for ticker in tickers:
	model = StockScreener(ticker=ticker)
	result = model.train()
	if result['buy_call']:
		buy_calls.append(ticker)
print(buy_calls)
print(time.time() - start)