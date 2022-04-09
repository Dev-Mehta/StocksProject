from model.model import StockModel, StockModelOffline, StockScreener, StocksToCsv
import yfinance as yf
import pandas as pd
from datetime import timedelta, datetime
import time
df = pd.read_csv('nifty100.csv')
tickers = df.Symbol.to_numpy()
main_df = []
for ticker in tickers:
	m = StockModel(ticker)
	result, dataframe, _ = m.train()
	main_df.append(dataframe)
	print(f"{ticker} Done")
	print(pd.DataFrame(main_df))
df = pd.DataFrame(main_df)
df.index = df.stock
df = df.sort_values(['returns'], ascending=False)
df.to_csv('backtest_results_70_30_online.csv')	