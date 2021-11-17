import yfinance as yf
tickers = [
	'SBILIFE',
	'MARUTI',
	'TATAMOTORS',
	'ITC',
	'ASIANPAINT',
	'POWERGRID',
	'NTPC',
	'INDUSINDBK',
	'TECHM',
	'BAJFINANCE',
	'SBIN',
	'TATACONSUM',
	'BAJAJFINSV',
	'LT',
	'INFY',
	'HDFCBANK',
	'WIPRO',
	'UPL'
]
for ticker in tickers:
	yf.Ticker(f'{ticker}.NS').history(period='max', actions=False).to_csv(f'data/{ticker}.csv')
	print(f'{ticker} Downloaded Data')