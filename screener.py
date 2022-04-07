import os, sys, django
sys.path.append("D:\Projects\StocksProject")
sys.path.append("D:\Projects\StockBlog")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stockmarket.settings")
django.setup()

from model.model import StockScreener
import pandas as pd
import time
df = pd.read_csv('nifty5.csv')
tickers = df.Symbol.to_numpy()
tickers.sort()
start = time.time()
buy_calls = []
for i in range(len(tickers)):
	try:
		buy_call = StockScreener(tickers[i]).train()['buy_call']
		if buy_call:
			buy_calls.append(tickers[i])
	except:
		pass
print(buy_calls)
print("Time taken for 5 stocks: ", time.time() - start)