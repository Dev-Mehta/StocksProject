import yfinance as yf
import pandas as pd
from datetime import timedelta, datetime
from model.model import StockModel
df = pd.read_csv('model/nifty100.csv')
tickers = df.Symbol.values.tolist()
main_df = pd.DataFrame()
outputs = []
for ticker in tickers:
	try:
		model = StockModel(ticker=ticker)
		result, df = model.train()
		outputs.append(df)
		print('Done for {}'.format(ticker))
	except KeyError:
		print('KeyError for {}'.format(ticker))
		continue
df = pd.DataFrame(outputs)
df.to_csv('backtest_results.csv')