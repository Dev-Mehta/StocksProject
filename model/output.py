import os, sys, django
sys.path.append("D:\Projects\StocksProject")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stockmarket.settings")
django.setup()
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
	data.index = data.Date
	buys = 0
	sells = 0
	entry = []
	exits = []
	for i in data.iterrows():
		item = i[1]
		if item['scores'] >= 11:
			entry.append(item['Date'])
			buys += 1
		if item['scores'] < 7:
			if buys > 0:
				if not sells + 1 > buys:
					date_buy = entry[-1]
					date_sell = item['Date']
					date_buy = pd.to_datetime(date_buy).date()
					date_sell = pd.to_datetime(date_sell).date()
					if date_sell > date_buy:
						exits.append(item['Date'])
						sells += 1
	trades = pd.DataFrame(columns=['Entry_Date','Exit_Date', 'Entry', 'Exit', 'profit'])
	for i in range(0,len(entry)):
		item = data.loc[entry[i]]
		try:
			exit_p = data.loc[exits[i]].Close
			trades = trades.append({'Entry_Date': item['Date'], 'Exit_Date':exits[i],'Entry': item['Close'], 'Exit': exit_p}, ignore_index=True)
		except IndexError:
			trades = trades.append({'Entry_Date': item['Date'], 'Exit_Date':None,'Entry': item['Close'], 'Exit': None}, ignore_index=True)
	trades.index = trades.Entry_Date
	trades.profit = 10*(trades.Exit - trades.Entry)
	trades.to_csv(f'results/{ticker}.csv')