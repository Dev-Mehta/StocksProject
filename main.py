from model.model import StockClassifier

tickers = ['BHEL', 'RELIANCE', 'GAIL', 'TCS', 'TECHM', 'INFY', 'LT'
,'VEDL', 'L&TFH', 'GODREJCP', 'LTI', 'GMRINFRA', 'IBULHSGFIN'
,'MARUTI', 'BAJFINANCE']
m = StockClassifier(tickers=tickers)
result = m.train()
buys = m.filterSell(3)
print(m.filterStock('bhel'))