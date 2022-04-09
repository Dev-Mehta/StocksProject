from functools import reduce
from itertools import islice
from time import time
from matplotlib import ticker
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
class TestFeed(bt.feeds.PandasData):
	lines = ('scores', )
	params = (('scores', 23),)
	# params = (('scores', 24),)
class TestFeedOffline(bt.feeds.PandasData):
	lines = ('scores', )
	# params = (('scores', 23),)
	params = (('scores', 24),)
orders = []
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
		self.cash_value = 500000
		self.cumprofit = 0.0
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
		self.cumprofit += trade.pnlcomm
		if trade.pnlcomm > 0:
			self.cash_value += int(trade.pnlcomm)
			if self.cumprofit > 0:
				if self.cumprofit < trade.pnlcomm:
					self.broker.add_cash(int(self.cumprofit // 2))	
				else:
					self.broker.add_cash(int(trade.pnlcomm // 2))
	def next(self):
		# Simply log the closing price of the series from the reference
		if self.order:
			return
		# Check if we are in the market
		if not self.position:
			# Not yet ... we MIGHT BUY if ...
			if self.scores[0] <= 40:
				# Keep track of the created order to avoid a 2nd order
				self.size = int(int((self.cash_value*0.5)) // self.dataclose[0])
				self.size = self.size - (self.size%50)
				self.order = self.buy(size=self.size, exectype=bt.Order.StopTrail, trailpercent=0.1)
				orders.append({"size":self.size, "price":self.dataclose[0], "date":self.datas[0].datetime.date(0)})
		else:		
			if self.scores[0] >= 60:
				self.order = self.sell(size=self.size)


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
				 'quantity': size, 'num_days': barlen, 'account_value':500000 + self.cumprofit})

class StockScreener():
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
				rsiValue = df[4][8]
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
			macd = [
				df[4][12],
				df[3][12],
				df[2][12],
				df[1][12],
				df[0][12],
			]
			try:
				date = macd.index(1)
				return 5 - date
			except IndexError:
				return 0
			except ValueError:
				return 0
		if indicator == 'MACD_BUY' and entry_type == 'long':
			macd = [
				df[4][16],
				df[3][16],
				df[2][16],
				df[1][16],
				df[0][16],
			]
			try:
				date = 1 in macd
				if date:
					return 5
				else:
					return 0
			except IndexError:
				return 0
		if indicator == 'EMA_BUY' and entry_type == 'long':
			ema = [
				df[4][18],
				df[3][18],
				df[2][18],
				df[1][18],
				df[0][18],
			]
			try:
				date = 1 in ema
				if date:
					return 5
				else:
					return 0
			except IndexError:
				return 0
		if indicator == 'EMA' and entry_type == 'long':
			ema_crossover = [
				df[4][14],
				df[3][14],
				df[2][14],
				df[1][14],
				df[0][14],
			]
			try:
				date = ema_crossover.index(1)
				return 5 - date
			except IndexError:
				return 0
			except ValueError:
				return 0
		if indicator == 'VOLUME' and entry_type == 'long':
			volume_buy = [
				df[4][22],
				df[3][22],
				df[2][22],
				df[1][22],
				df[0][22],
			]
			try:
				date = volume_buy.index(1)
				return 5 - date
			except IndexError:
				return 0
			except ValueError:
				return 0
		return None

	def window(self, seq, n=5):
		it = iter(seq)
		result = tuple(islice(it, n))
		if len(result) == n:
			yield result
		for elem in it:
			result = result[1:] + (elem,)
			yield result
	def format_indian(self, t):
		dic = {
			4:'Thousand',
			5:'Lakh',
			6:'Lakh',
			7:'Crore',
			8:'Crore',
			9:'Arab'
		}
		y = 10
		len_of_number = len(str(t))
		save = t
		z=y
		while(t!=0):
			t=int(t/y)
			z*=10

		zeros = len(str(z)) - 3
		if zeros>3:
			if zeros%2!=0:
				string = str(save)+": "+str(save/(z/100))[0:4]+" "+dic[zeros]
			else:   
				string = str(save)+": "+str(save/(z/500000))[0:4]+" "+dic[zeros]
			return string
		return str(save)+": "+str(save)

	def train(self, test=False):
		if self.ticker != None:
			start = (datetime.now() - timedelta(days=300)).date()
			end = datetime.now().date()
			
			data = yf.Ticker(self.ticker + '.NS').history(start=start, end=end, actions=False)
			
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
			
			dataf = data.to_numpy()
			
			len_data = len(data.index.values)-5
			
			start = time()
			
			for i in range(len_data):
				df = dataf[i:i+5]
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
			data['scores'] = data['scores'] * 5
			data['buy_today'] = np.where(data.scores <= 30, 1, 0)
			data['sell_today'] = np.where(data.scores >= 70, 1, 0)
			result = {}
			last_row = data.iloc[-1,:]
			rsi_buy = last_row['rsi_buy']
			macd_buy = 1 if last_row['macd'] > last_row['macdSignal']  else 0
			ema_buy = 1 if last_row['5EMA'] > last_row['26EMA'] else 0
			volume_buy = last_row['volume_buy']
			rsi_sell = last_row['rsi_sell']
			macd_sell = last_row['macd_crossunder']
			ema_sell = last_row['ema_crossunder']
			volume_sell = last_row['volume_sell']
			result['score'] = last_row['scores']
			buying_factors = {'rsi_buy':rsi_buy, 'macd_buy':macd_buy, 'ema_buy':ema_buy, 'volume_buy':volume_buy}
			selling_factors = {'rsi_sell':rsi_sell, 'macd_sell':macd_sell, 'ema_sell':ema_sell, 'volume_sell':volume_sell}
			result['buying_factors'] = buying_factors
			result['selling_factors'] = selling_factors
			result['buy_call'] = data.buy_today[-1]
			result['sell_call'] = data.sell_today[-1]
			return result

class StocksToCsv:
	tickers = None
	
	def __init__(self, tickers) -> None:
		self.tickers = tickers 
	
	def download(self):
		if self.tickers != None:
			for i in self.tickers:
				ticker = i.upper()
				data = yf.Ticker(ticker + '.NS').history(period='max',actions=False)
				data.to_csv(f'data/{ticker}.csv')
class StockModel:
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
				rsiValue = df[4][8]
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
			macd = [
				df[4][12],
				df[3][12],
				df[2][12],
				df[1][12],
				df[0][12],
			]
			try:
				date = macd.index(1)
				return 5 - date
			except IndexError:
				return 0
			except ValueError:
				return 0
		if indicator == 'MACD_BUY' and entry_type == 'long':
			macd = [
				df[4][16],
				df[3][16],
				df[2][16],
				df[1][16],
				df[0][16],
			]
			try:
				date = 1 in macd
				if date:
					return 5
				else:
					return 0
			except IndexError:
				return 0
		if indicator == 'EMA_BUY' and entry_type == 'long':
			ema = [
				df[4][18],
				df[3][18],
				df[2][18],
				df[1][18],
				df[0][18],
			]
			try:
				date = 1 in ema
				if date:
					return 5
				else:
					return 0
			except IndexError:
				return 0
		if indicator == 'EMA' and entry_type == 'long':
			ema_crossover = [
				df[4][14],
				df[3][14],
				df[2][14],
				df[1][14],
				df[0][14],
			]
			try:
				date = ema_crossover.index(1)
				return 5 - date
			except IndexError:
				return 0
			except ValueError:
				return 0
		if indicator == 'VOLUME' and entry_type == 'long':
			volume_buy = [
				df[4][22],
				df[3][22],
				df[2][22],
				df[1][22],
				df[0][22],
			]
			try:
				date = volume_buy.index(1)
				return 5 - date
			except IndexError:
				return 0
			except ValueError:
				return 0
		return None

	def window(self, seq, n=5):
		it = iter(seq)
		result = tuple(islice(it, n))
		if len(result) == n:
			yield result
		for elem in it:
			result = result[1:] + (elem,)
			yield result
	def format_indian(self, t):
		dic = {
			4:'Thousand',
			5:'Lakh',
			6:'Lakh',
			7:'Crore',
			8:'Crore',
			9:'Arab'
		}
		y = 10
		len_of_number = len(str(t))
		save = t
		z=y
		while(t!=0):
			t=int(t/y)
			z*=10

		zeros = len(str(z)) - 3
		if zeros>3:
			if zeros%2!=0:
				string = str(save)+": "+str(save/(z/100))[0:4]+" "+dic[zeros]
			else:   
				string = str(save)+": "+str(save/(z/500000))[0:4]+" "+dic[zeros]
			return string
		return str(save)+": "+str(save)

	def train(self, test=False):
		if self.ticker != None:
			start = (datetime.now() - timedelta(days=2500)).date()
			end = datetime.now().date()
			
			data = yf.Ticker(self.ticker + '.NS').history(period='max', actions=False)
			initial_year = data.index[0]
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
			dataf = data.to_numpy()
			len_data = len(data.index.values)-5
			start = time()
			for i in range(len_data):
				df = dataf[i:i+5]
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
			data['scores'] = data['scores'] * 5
			data['buy_today'] = np.where(data.scores <= 30, 1, 0)
			data['sell_today'] = np.where(data.scores >= 70, 1, 0)
			# data.to_csv('output/TATASTEEL.csv')
			# data.Date = pd.to_datetime(data.Date)
			# data.index = data.Date
			cerebro = bt.Cerebro()
			cerebro.addstrategy(TestStrategy)
			trade_data = data.dropna()
			trade_data = TestFeed(dataname=trade_data)
			cerebro.adddata(trade_data)
			cerebro.broker.setcash(500000.0)
			cerebro.broker.setcommission(commission=0.002)
			cerebro.addanalyzer(trade_list, _name='trade_list')
			strats = cerebro.run(tradehistory=True)
			tl = strats[0].analyzers.trade_list.get_analysis()
			cumprofit = strats[0].analyzers.trade_list.cumprofit
			last_order = orders[-1]
			
			data = data.iloc[-100:,:]
			data['dates'] = data.index.values
			data['dates'] = data['dates'].apply(lambda x: str(x.date()).split('-')[2])
			scoresX = data.iloc[:,-4:-3]
			scoresX.drop(scoresX.index[0], inplace=True)
			datesY = data["scores"].shift(1).dropna()
			self.model.fit(np.array(datesY).reshape(-1, 1), scoresX)
			yhat = self.model.predict([[(timedelta(days=1)+datetime.now()).day]]) #predict score for next day
			data.iloc[:,-2:]
			self.regressor.fit(np.asarray(data['scores']).reshape(-1, 1),data['Close'])
			result = {}
			result['price'] = yhat[0][0]
			last_row = data.iloc[-1,:]
			rsi_buy = last_row['rsi_buy']
			macd_buy = 1 if last_row['macd'] > last_row['macdSignal']  else 0
			ema_buy = 1 if last_row['5EMA'] > last_row['26EMA'] else 0
			volume_buy = last_row['volume_buy']
			rsi_sell = last_row['rsi_sell']
			macd_sell = last_row['macd_crossunder']
			ema_sell = last_row['ema_crossunder']
			volume_sell = last_row['volume_sell']
			result['score'] = last_row['scores']
			if last_order['date'] != tl[-1]['buy_date']:
				result['last_order'] = last_order
			else:
				result['last_order'] = None
			buying_factors = {'rsi_buy':rsi_buy, 'macd_buy':macd_buy, 'ema_buy':ema_buy, 'volume_buy':volume_buy}
			selling_factors = {'rsi_sell':rsi_sell, 'macd_sell':macd_sell, 'ema_sell':ema_sell, 'volume_sell':volume_sell}
			result['buying_factors'] = buying_factors
			result['selling_factors'] = selling_factors
			result['backtest_start'] = start
			result['backtest_end'] = end
			result['backtest_results'] = tl
			result['ending_value'] = 500000 + cumprofit
			result['buy_call'] = data.buy_today[-1]
			result['sell_call'] = data.sell_today[-1]
			backtest_result = pd.DataFrame(result['backtest_results'])
			ending_value = result['ending_value']
			pnl = None
			try:
				pnl = backtest_result['pnl']
			except KeyError:
				pass
			returns = ((ending_value - 500000) / 500000) * 100
			accuracy = (pnl[pnl > 0].count() / pnl.count()) * 100
			
			profit = pnl.sum()
			avg_pl = profit / len(pnl)
			avg_profit = pnl[pnl > 0].mean()
			avg_loss = pnl[pnl < 0].mean()
			max_profit = pnl.max()
			max_loss = pnl.min()
			dataframe = {}
			dataframe['stock'] = self.ticker
			dataframe['initial_capital'] = 500000
			dataframe['ending_value'] = ending_value
			dataframe['returns'] = returns
			dataframe['accuracy'] = accuracy
			dataframe['profit'] = profit
			dataframe['avg_pl'] = avg_pl
			dataframe['avg_profit'] = avg_profit
			dataframe['avg_loss'] = avg_loss
			dataframe['max_profit'] = max_profit
			dataframe['max_loss'] = max_loss
			dataframe['trade_list'] = tl
			return result, dataframe, initial_year

class StockModelOffline:
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
				rsiValue = df[4][8]
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
			macd = [
				df[4][12],
				df[3][12],
				df[2][12],
				df[1][12],
				df[0][12],
			]
			try:
				date = macd.index(1)
				return 5 - date
			except IndexError:
				return 0
			except ValueError:
				return 0
		if indicator == 'MACD_BUY' and entry_type == 'long':
			macd = [
				df[4][16],
				df[3][16],
				df[2][16],
				df[1][16],
				df[0][16],
			]
			try:
				date = 1 in macd
				if date:
					return 5
				else:
					return 0
			except IndexError:
				return 0
		if indicator == 'EMA_BUY' and entry_type == 'long':
			ema = [
				df[4][18],
				df[3][18],
				df[2][18],
				df[1][18],
				df[0][18],
			]
			try:
				date = 1 in ema
				if date:
					return 5
				else:
					return 0
			except IndexError:
				return 0
		if indicator == 'EMA' and entry_type == 'long':
			ema_crossover = [
				df[4][14],
				df[3][14],
				df[2][14],
				df[1][14],
				df[0][14],
			]
			try:
				date = ema_crossover.index(1)
				return 5 - date
			except IndexError:
				return 0
			except ValueError:
				return 0
		if indicator == 'VOLUME' and entry_type == 'long':
			volume_buy = [
				df[4][22],
				df[3][22],
				df[2][22],
				df[1][22],
				df[0][22],
			]
			try:
				date = volume_buy.index(1)
				return 5 - date
			except IndexError:
				return 0
			except ValueError:
				return 0
		return None

	def window(self, seq, n=5):
		it = iter(seq)
		result = tuple(islice(it, n))
		if len(result) == n:
			yield result
		for elem in it:
			result = result[1:] + (elem,)
			yield result
	def format_indian(self, t):
		dic = {
			4:'Thousand',
			5:'Lakh',
			6:'Lakh',
			7:'Crore',
			8:'Crore',
			9:'Arab'
		}
		y = 10
		len_of_number = len(str(t))
		save = t
		z=y
		while(t!=0):
			t=int(t/y)
			z*=10

		zeros = len(str(z)) - 3
		if zeros>3:
			if zeros%2!=0:
				string = str(save)+": "+str(save/(z/100))[0:4]+" "+dic[zeros]
			else:   
				string = str(save)+": "+str(save/(z/500000))[0:4]+" "+dic[zeros]
			return string
		return str(save)+": "+str(save)

	def train(self, test=False):
		if self.ticker != None:
			start = (datetime.now() - timedelta(days=2500)).date()
			end = datetime.now().date()
			
			data = pd.read_csv(f'data/{self.ticker}.csv')
			initial_year = data.index[0]
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
			dataf = data.to_numpy()
			len_data = len(data.index.values)-5
			start = time()
			for i in range(len_data):
				df = dataf[i:i+5]
				rsiScore = self.get_score(df, indicator='rsi')
				macdScore = self.get_score(df, indicator='macd')
				emaScore = self.get_score(df, indicator='ema')
				volumeScore = self.get_score(df, indicator='volume')
				macdBuyScore = self.get_score(df, indicator='macd_buy', entry_type='long')
				emaBuyScore = self.get_score(df, indicator='ema_buy', entry_type='long')
				scores = rsiScore + macdScore + emaScore + volumeScore + macdBuyScore + emaBuyScore
				scoresL.append(scores)
			data['scores'] = scoresL
			data['scores'] = data.scores.ewm(span=3).mean()
			data['scores'] = data['scores'].apply(lambda x: x*5)
			data['buy_today'] = np.where(data.scores <= 30, 1, 0)
			data['sell_today'] = np.where(data.scores >= 70, 1, 0)
			# data.to_csv('output/TATASTEEL.csv')
			data.Date = pd.to_datetime(data.Date)
			data.index = data.Date
			cerebro = bt.Cerebro()
			cerebro.addstrategy(TestStrategy)
			trade_data = data.dropna()
			trade_data = TestFeedOffline(dataname=trade_data)
			cerebro.adddata(trade_data)
			cerebro.broker.setcash(500000.0)
			cerebro.broker.setcommission(commission=0.002)
			cerebro.addanalyzer(trade_list, _name='trade_list')
			strats = cerebro.run(tradehistory=True)
			tl = strats[0].analyzers.trade_list.get_analysis()
			cumprofit = strats[0].analyzers.trade_list.cumprofit
			last_order = orders[-1]
			
			data = data.iloc[-100:,:]
			data['dates'] = data.index.values
			data['dates'] = data['dates'].apply(lambda x: str(x.date()).split('-')[2])
			scoresX = data.iloc[:,-4:-3]
			scoresX.drop(scoresX.index[0], inplace=True)
			datesY = data["scores"].shift(1).dropna()
			self.model.fit(np.array(datesY).reshape(-1, 1), scoresX)
			yhat = self.model.predict([[(timedelta(days=1)+datetime.now()).day]]) #predict score for next day
			data.iloc[:,-2:]
			self.regressor.fit(np.asarray(data['scores']).reshape(-1, 1),data['Close'])
			result = {}
			result['price'] = yhat[0][0]
			last_row = data.iloc[-1,:]
			rsi_buy = last_row['rsi_buy']
			macd_buy = 1 if last_row['macd'] > last_row['macdSignal']  else 0
			ema_buy = 1 if last_row['5EMA'] > last_row['26EMA'] else 0
			volume_buy = last_row['volume_buy']
			rsi_sell = last_row['rsi_sell']
			macd_sell = last_row['macd_crossunder']
			ema_sell = last_row['ema_crossunder']
			volume_sell = last_row['volume_sell']
			result['score'] = last_row['scores']
			if last_order['date'] != tl[-1]['buy_date']:
				result['last_order'] = last_order
			else:
				result['last_order'] = None
			buying_factors = {'rsi_buy':rsi_buy, 'macd_buy':macd_buy, 'ema_buy':ema_buy, 'volume_buy':volume_buy}
			selling_factors = {'rsi_sell':rsi_sell, 'macd_sell':macd_sell, 'ema_sell':ema_sell, 'volume_sell':volume_sell}
			result['buying_factors'] = buying_factors
			result['selling_factors'] = selling_factors
			result['backtest_start'] = start
			result['backtest_end'] = end
			result['backtest_results'] = tl
			result['ending_value'] = 500000 + cumprofit
			result['buy_call'] = data.buy_today[-1]
			result['sell_call'] = data.sell_today[-1]
			backtest_result = pd.DataFrame(result['backtest_results'])
			ending_value = result['ending_value']
			pnl = None
			try:
				pnl = backtest_result['pnl']
			except KeyError:
				pass
			returns = ((ending_value - 500000) / 500000) * 100
			accuracy = (pnl[pnl > 0].count() / pnl.count()) * 100
			
			profit = pnl.sum()
			avg_pl = profit / len(pnl)
			avg_profit = pnl[pnl > 0].mean()
			avg_loss = pnl[pnl < 0].mean()
			max_profit = pnl.max()
			max_loss = pnl.min()
			dataframe = {}
			dataframe['stock'] = self.ticker
			dataframe['initial_capital'] = 500000
			dataframe['ending_value'] = ending_value
			dataframe['returns'] = returns
			dataframe['accuracy'] = accuracy
			dataframe['profit'] = profit
			dataframe['avg_pl'] = avg_pl
			dataframe['avg_profit'] = avg_profit
			dataframe['avg_loss'] = avg_loss
			dataframe['max_profit'] = max_profit
			dataframe['max_loss'] = max_loss
			return result, dataframe, initial_year
