import pandas as pd
import talib as ta
import numpy as np
from pandas import DataFrame
def get_score(df: DataFrame, indicator: str, entry_type='long'):
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
data = pd.read_csv('data/TATASTEEL.csv')
data.reset_index()
data.Date = pd.to_datetime(data.Date)
data.index = data.Date
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
	rsiScore = get_score(df, indicator='rsi')
	macdScore = get_score(df, indicator='macd')
	emaScore = get_score(df, indicator='ema')
	volumeScore = get_score(df, indicator='volume')
	macdBuyScore = get_score(df, indicator='macd_buy', entry_type='long')
	emaBuyScore = get_score(df, indicator='ema_buy', entry_type='long')
	scores = rsiScore + macdScore + emaScore + volumeScore + macdBuyScore + emaBuyScore
	scoresL.append(scores)
data['scores'] = scoresL
data['scores'] = data.scores.ewm(span=5).mean()
data.to_csv('output/TATASTEEL.csv')