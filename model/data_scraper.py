import yfinance as yf
import pandas as pd
from datetime import timedelta, datetime
df = pd.read_csv('nifty100.csv')
tickers = df.Symbol.values.tolist()
start = (datetime.now() - timedelta(days=100000)).date()
end = datetime.now().date()
tickers = ['TATASTEEL']
for ticker in tickers:
	yf.Ticker(f'{ticker}.NS').history(period='max', actions=False).to_csv(f'data/{ticker}.csv')
	print(f'{ticker} Downloaded Data')