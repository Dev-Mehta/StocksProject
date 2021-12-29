import pandas as pd
df = pd.read_csv('nifty100.csv')
tickers = df.Symbol.values.tolist()
net_profit = 0
detailed = {}
for ticker in tickers:
	data = pd.read_csv(f'results/{ticker}.csv')
	net_profit += data.profit.sum()
	detailed[ticker] = data.profit.sum()
print(net_profit)
print(detailed)