from datetime import timedelta, datetime
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
tick_accuracy = []
avg_accuracy = 0
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
			if len(entry) == len(exits):
				if not len(entry) > 0:
					entry.append(item['Date'])
					buys += 1
				elif not datetime.strptime(item.Date, "%Y-%m-%d") - datetime.strptime(entry[-1], "%Y-%m-%d") <= timedelta(days=5):
					entry.append(item['Date'])
					buys += 1
		if item['scores'] <= 7:
			if buys > 0:
				if not sells + 1 > buys:
					date_buy = entry[-1]
					date_sell = item['Date']
					date_buy = pd.to_datetime(date_buy).date()
					date_sell = pd.to_datetime(date_sell).date()
					if date_sell > date_buy:
						if not len(exits) > 0:
							exits.append(item['Date'])
							sells += 1
						elif not datetime.strptime(item.Date, "%Y-%m-%d") - datetime.strptime(exits[-1], "%Y-%m-%d") <= timedelta(days=5):
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
	trades.profit = 10*(trades.Exit - trades.Entry)
	if len(trades) > 100:
		trades = trades[100:-1]
	elif len(trades) > 50:
		trades = trades[50:-1]
	profits = trades.profit[trades.profit > 0].count()
	losses = trades.profit[trades.profit < 0].count()
	avg_loss = trades.profit[trades.profit < 0].mean()
	avg_profit = trades.profit[trades.profit > 0].mean()
	max_loss = trades.profit[trades.profit < 0].min()
	max_profit = trades.profit[trades.profit > 0].max()
	accuracy = (profits/(profits+losses))*100
	trades.to_csv(f'results/{ticker}.csv')

	tick_accuracy.append(accuracy)
	avg_accuracy = sum(tick_accuracy)/len(tick_accuracy)
	with open("results.txt", "a") as f:
		f.write(f'{ticker} accuracy: {accuracy}\n')
		f.write(f'{ticker} avg. loss: {avg_loss:.2f}' + '\n')
		f.write(f'{ticker} avg. profit: {avg_profit:.2f}' + '\n')
		f.write(f'{ticker} max. loss: {max_loss:.2f}' + '\n')
		f.write(f'{ticker} max. profit: {max_profit:.2f}' + '\n')
