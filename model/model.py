from pandas.core.frame import DataFrame
import yfinance as yf
import pandas as pd
import numpy as np
import talib as ta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta
import requests, json
import backtrader as bt
from watchlist.models import Stock

class TestFeed(bt.feeds.PandasData):
	lines = ('scores', )
	params = (('scores', 23),)

class TestStrategy(bt.Strategy):

	def log(self, txt, dt=None):
		''' Logging function for this strategy'''
		dt = dt or self.datas[0].datetime.date(0)
		print('%s, %s' % (dt.isoformat(), txt))

	def __init__(self):
		# Keep a reference to the "close" line in the data[0] dataseries
		self.dataclose = self.datas[0].close
		self.order = None
		self.buyprice = None
		self.buycomm = None
		self.scores = self.datas[0].scores
		self.trades = None
		self.size = 10
	def notify_order(self, order):
		if order.status in [order.Submitted, order.Accepted]:
			# Buy/Sell order submitted/accepted to/by broker - Nothing to do
			return

		# Check if an order has been completed
		# Attention: broker could reject order if not enough cash
		if order.status in [order.Completed]:
			if order.isbuy():
				self.buyprice = order.executed.price
				self.buycomm = order.executed.comm	
			self.bar_executed = len(self)


		# Write down: no pending order
		self.order = None
	def notify_trade(self, trade):
		if not trade.isclosed:
			return
		

	def next(self):
		# Simply log the closing price of the series from the reference
		if self.order:
			return
		# Check if we are in the market
		if not self.position:
			# Not yet ... we MIGHT BUY if ...
			if self.scores[0] > 14:
					# Keep track of the created order to avoid a 2nd order
					self.order = self.buy()
		else:
			# Already in the market ... we might sell
			if len(self) >= (self.bar_executed + 7):
				if self.scores[0] <= 9 and self.scores >= 4:
					self.order = self.sell()
				
class trade_list(bt.Analyzer):

	def get_analysis(self):

		return self.trades


	def __init__(self):

		self.trades = []
		self.cumprofit = 0.0


	def notify_trade(self, trade):

		if trade.isclosed:

			brokervalue = self.strategy.broker.getvalue()

			dir = 'short'
			if trade.history[0].event.size > 0: dir = 'long'

			pricein = trade.history[len(trade.history)-1].status.price
			priceout = trade.history[len(trade.history)-1].event.price
			datein = bt.num2date(trade.history[0].status.dt)
			dateout = bt.num2date(trade.history[len(trade.history)-1].status.dt)
			if trade.data._timeframe >= bt.TimeFrame.Days:
				datein = datein.date()
				dateout = dateout.date()

			pcntchange = 100 * priceout / pricein - 100
			pnl = trade.history[len(trade.history)-1].status.pnlcomm
			pnlpcnt = 100 * pnl / brokervalue
			barlen = trade.history[len(trade.history)-1].status.barlen
			pbar = pnl / barlen
			self.cumprofit += pnl

			size = value = 0.0
			for record in trade.history:
				if abs(size) < abs(record.status.size):
					size = record.status.size
					value = record.status.value

			highest_in_trade = max(trade.data.high.get(ago=0, size=barlen+1))
			lowest_in_trade = min(trade.data.low.get(ago=0, size=barlen+1))
			hp = 100 * (highest_in_trade - pricein) / pricein
			lp = 100 * (lowest_in_trade - pricein) / pricein
			if dir == 'long':
				mfe = hp
				mae = lp
			if dir == 'short':
				mfe = -lp
				mae = -hp
			self.trades.append({'id': trade.ref, 'ticker': trade.data._name, 'Entry Type': dir,
				 'buy_date': datein, 'buy_price': pricein, 'sell_date': dateout, 'sell_price': priceout,
				 'change_pct': round(pcntchange, 2), 'pnl': pnl, 'pnl_pct': round(pnlpcnt, 2),
				 'quantity': size, 'num_days': barlen})

class StockClassifier:
	ticker = None
	model = LinearRegression()
	regressor = RandomForestRegressor(n_estimators = 100, random_state = 0)
	def __init__(self, ticker) -> None:
		self.ticker = ticker.upper() 
	
	"""
	Parameters
	----------
	df -> Dataframe of stock's historical data
	indicator -> mathematical formula to make an indicator on
		Supported indicators:
			rsi -> Relative Strength Indicator
			macd -> Moving Average Convergence Divergence
			ema -> Exponential Moving Average
			volume -> It's not actually an indicator but we are using it to analyse
			price volume data by correlating price movements with volume.
	entry_type -> The view of underlying stock.
		long -> We take long entry for bullishness
		short -> We take short entry for bearishness
	"""
	def get_score(self, df: DataFrame, indicator: str, entry_type='long'):
		indicator = indicator.upper()
	
		if indicator == 'RSI' and entry_type == 'long':
			"""
			General Strategy with RSI:
				If RSI Value is >= 70:
					It is considered that the stock is overpriced as
					the stock is overbought in the last few trading sessions.
					
					Increasing RSI is generally considered a negative sign,
					and the stock is expected to be bearish.
				If RSI Value is <= 30:
					It is considered that the stock is underpriced as
					the stock is oversold in the last few trading sessions.

					Decreasing RSI is generally considered as a positive sign,
					and the stock is expected to be bullish in upcoming trading sessions.

			Our strategy with RSI:
				If RSI Value in range of 60-70
					We consider this the best range of RSI as if the stock has
					RSI value of >=60 and <= 70. It is not overbought but it actually
					deserves to be a performing stock.

					We expect the stock to perform more in upcoming trading sessions.

				If RSI Value in range of 70-80
					We consider this the next best range of RSI. If the stock is in 
					ragne of this we can expect bullishness but now the upmove is
					considered to be weak as the move may have came to an end as 
					RSI is already this much high.
				
				If RSI Value in range of >= 80
					We consider this as a weakening score and a potential threat, 
					as the stock might be actually overperforming. 

					This is just like a typical overbought zone.
				
				If RSI Value in range 50-60
					We consider this as a moderate range, and the stock might
					start performing from here. So we return the score with value of 2.

				If any given condition is not matched we simply return the score value of 0.
			"""
			try:
				rsiValue = df.rsi.head(1).values[0]
				if rsiValue in range(60,70):
					return 5
				elif rsiValue in range(70,80):
					return 4
				elif rsiValue >= 80:
					return 3
				elif rsiValue in range(50,60):
					return 2
				else:
					return 0
			except IndexError:
				return 0
		"""
			General Strategy with MACD:
				In MACD there are two components which are calculated.
				MACD Signal and MACD.
				If value of MACD is greaten than MACD Signal, 
					it is considered a bullish crossover and the stock might
					start performing from here.
				If value of MACD is less than MACD Signal,
					it is considered a bearish crossover and the stock might
					start falling from here.

			Our Strategy with MACD:
				We go along with the general strategy but with some modifications.
				Instead of simply checking the condition of MACD > Macd Signal, 
				we check when the crossover happened.

				The nearer the crossover with today's date the more strength the
				buy signal has.
		"""
		if indicator == 'MACD' and entry_type == 'long':
			macd = df.macd_crossover
			try:
				date = macd.iloc[list(np.where(df["macd_crossover"] == 1)[0])].index.values[0]
				date = pd.to_datetime(date)
				dates = df.index.values
				for i in range(0,len(dates)):
					if pd.to_datetime(dates[i]).date() == date:
						return 5 - i
				return 0
			except IndexError:
				return 0
		if indicator == 'MACD_BUY' and entry_type == 'long':
			macd = df.macd_buy
			try:
				date = macd.iloc[list(np.where(df["macd_buy"] == 1)[0])].index.values[0]
				date = pd.to_datetime(date)
				dates = df.index.values
				for i in range(0,len(dates)):
					if pd.to_datetime(dates[i]).date() == date:
						return 5 - i
				return 0
			except IndexError:
				return 0
		if indicator == 'EMA_BUY' and entry_type == 'long':
			try:
				date = df.ema_buy.iloc[list(np.where(df["ema_buy"] == 1)[0])].index.values[0]
				date = pd.to_datetime(date)
				dates = df.index.values
				for i in range(0,len(dates)):
					if pd.to_datetime(dates[i]).date() == date:
						return 5 - i
				return 0
			except IndexError:
				return 0
		if indicator == 'EMA' and entry_type == 'long':
			try:
				date = df.ema_crossover.iloc[list(np.where(df["ema_crossover"] == 1)[0])].index.values[0]
				date = pd.to_datetime(date)
				dates = df.index.values
				for i in range(0,len(dates)):
					if pd.to_datetime(dates[i]).date() == date:
						return 5 - i
				return 0
			except IndexError:
				return 0
		if indicator == 'VOLUME' and entry_type == 'long':
			try:
				date = df.volume_buy.iloc[list(np.where(df["volume_buy"] == 1)[0])].index.values[0]
				date = pd.to_datetime(date)
				dates = df.index.values
				for i in range(0,len(dates)):
					if pd.to_datetime(dates[i]).date() == date:
						return 5 - i
				return 0
			except IndexError:
				return 0
		return None

	def train(self, test=False):
		if self.ticker != None:
			start = (datetime.now() - timedelta(days=2500)).date()
			end = datetime.now().date()
			data = yf.Ticker(self.ticker+'.NS').history(period='max',actions=False)
			data['5EMA'] = pd.Series.ewm(data['Close'], span=5).mean()
			data['26EMA'] = pd.Series.ewm(data['Close'], span=26).mean()
			data['rsi'] = ta.RSI(data['Close'].values, timeperiod=14)

			data['macd'], data['macdSignal'], data['macdHist'] = ta.MACD(data.Close.values, fastperiod=12, slowperiod=26, signalperiod=9)

			data['macd_crossover'] = np.where(((data.macd > data.macdSignal) & (data.macd.shift(1) < data.macdSignal.shift(1))), 1, 0)
			data['macd_crossunder'] = np.where(((data.macd < data.macdSignal) & (data.macd.shift(1) > data.macdSignal.shift(1))), 1, 0)
			data['ema_crossover'] = np.where(((data['5EMA'].shift(1) <= data['26EMA'].shift(1)) & (data['5EMA'] > data['26EMA'] )), 1, 0)
			data['ema_crossunder'] = np.where(((data['5EMA'].shift(1) >= data['26EMA'].shift(1)) & (data['5EMA'] < data['26EMA'] )), 1, 0)
			data['macd_buy'] = np.where((data.macd > data.macdSignal), 1, 0)
			data['macd_sell'] = np.where((data.macd < data.macdSignal), 1, 0)
			data['ema_buy'] = np.where((data['5EMA'] > data['26EMA']), 1, 0)
			data['ema_sell'] = np.where((data['5EMA'] < data['26EMA']), 1, 0)
			data['rsi_buy'] = np.where(data.rsi >= 60, 1, 0)
			data['rsi_sell'] = np.where(data.rsi <= 40, 1, 0)

			data['volume_buy'] = np.where((data.Volume > data.Volume.ewm(span=5).mean()) & (data.Close > data.Close.shift(1)), 1, 0)
			data['volume_sell'] = np.where((data.Volume > data.Volume.ewm(span=5).mean()) & (data.Close < data.Close.shift(1)), 1, 0)
			
			scoresL = [0,0,0,0,0]
			for i in range(len(data.index.values)-5):
				df = data[i:i+5]
				rsiScore = self.get_score(df, indicator='rsi')
				macdScore = self.get_score(df, indicator='macd')
				emaScore = self.get_score(df, indicator='ema')
				volumeScore = self.get_score(df, indicator='volume')
				macdBuyScore = self.get_score(df, indicator='macd_buy', entry_type='long')
				emaBuyScore = self.get_score(df, indicator='ema_buy', entry_type='long')
				scores = rsiScore + macdScore + emaScore + volumeScore + macdBuyScore + emaBuyScore
				scoresL.append(scores)
			data['scores'] = scoresL
			data['scores'] = data.scores.ewm(span=5).mean()
			cerebro = bt.Cerebro()
			cerebro.addstrategy(TestStrategy)
			trade_data = data.dropna()
			trade_data = TestFeed(dataname=trade_data)
			cerebro.adddata(trade_data)
			cerebro.broker.setcash(100000.0)
			cerebro.broker.setcommission(commission=0.002)
			cerebro.addsizer(bt.sizers.SizerFix, stake=50)
			cerebro.addanalyzer(trade_list, _name='trade_list')
			strats = cerebro.run(tradehistory=True)
			tl = strats[0].analyzers.trade_list.get_analysis()
			s, created = Stock.objects.get_or_create(name=self.ticker)

			if created:
				s.backtest_result = str(json.dumps(tl))
				s.save()
			data = data.iloc[-100:,:]
			data['dates'] = data.index.values
			data['dates'] = data['dates'].apply(lambda x: str(x.date()).split('-')[2])
			scoresX = data.iloc[:,-2:-1]
			datesY = data["dates"]
			datesY = datesY.astype(int)
			self.model.fit(np.array(datesY).reshape(-1, 1), scoresX)
			yhat = self.model.predict([[(timedelta(days=1)+datetime.now()).day]]) #predict score for next day
			data.iloc[:,-2:]
			self.regressor.fit(np.asarray(data['scores']).reshape(-1, 1),data['Close'])
			result = {}
			result['price'] = self.regressor.predict(yhat)[0]
			last_row = data.iloc[-1,:]
			rsi_buy = last_row['rsi_buy']
			macd_buy = 1 if last_row['macd'] > last_row['macdSignal']  else 0
			ema_buy = 1 if last_row['5EMA'] > last_row['26EMA'] else 0
			volume_buy = last_row['volume_buy']
			rsi_sell = last_row['rsi_sell']
			macd_sell = last_row['macd_crossunder']
			ema_sell = last_row['ema_crossunder']
			volume_sell = last_row['volume_sell']
			buying_factors = {'rsi_buy':rsi_buy, 'macd_buy':macd_buy, 'ema_buy':ema_buy, 'volume_buy':volume_buy}
			selling_factors = {'rsi_sell':rsi_sell, 'macd_sell':macd_sell, 'ema_sell':ema_sell, 'volume_sell':volume_sell}
			result['buying_factors'] = buying_factors
			result['selling_factors'] = selling_factors
			result['backtest_start'] = start
			result['backtest_end'] = end
			result['backtest_results'] = tl
			return result

