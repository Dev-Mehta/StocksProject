import os, sys, django
sys.path.append("D:\Projects\StocksProject")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stockmarket.settings")
django.setup()
import mplfinance as mpf
import pandas as pd
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
	data = pd.read_csv(f'output/{ticker}.csv')
	data.index = pd.to_datetime(data.Date)
	s = mpf.make_addplot(data.scores, color='#00ff00', title='Scores')
	mpf.plot(data, addplot=s,type='line',style='yahoo', volume=False, title=ticker)