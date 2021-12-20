import yfinance as yf
tickers = [
	'RELIANCE',
	'TATASTEEL',
	'TATAPOWER'
]
for ticker in tickers:
	yf.Ticker(f'{ticker}.NS').history(period='max', actions=False).to_csv(f'data/{ticker}.csv')
	print(f'{ticker} Downloaded Data')