from pandas.core.frame import DataFrame
import yfinance as yf
import pandas as pd
import numpy as np
import talib as ta
import seaborn

	
def get_score(df: DataFrame, indicator: str, entry_type='long'):
	indicator = indicator.upper()
	if indicator == 'RSI' and entry_type == 'long':
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

def train(ticker: str):
	data = pd.read_csv(f'data/{ticker}.csv')
	data.set_index('Date', inplace=True)

	data['5EMA'] = pd.Series.ewm(data['Close'], span=5).mean()

	data['26EMA'] = pd.Series.ewm(data['Close'], span=26).mean()

	data['rsi'] = ta.RSI(data['Close'].values, timeperiod=14)

	data['macd'], data['macdSignal'], data['macdHist'] = ta.MACD(data.Close.values, fastperiod=12, slowperiod=26, signalperiod=9)

	data['macd_crossover'] = np.where(data.macd > data.macdSignal, 1, 0)
	data['macd_crossunder'] = np.where((data.macd < data.macdSignal), 1, 0)
	data['ema_crossover'] = np.where(data['5EMA'] > data['26EMA'], 1, 0)
	data['ema_crossunder'] = np.where(data['5EMA'] < data['26EMA'], 1, 0)

	data['rsi_buy'] = np.where(data.rsi > 60, 1, 0)
	data['rsi_sell'] = np.where(data.rsi < 40, 1, 0)

	data['volume_buy'] = np.where((data.Volume > data.Volume.ewm(span=5).mean()) & (data.Close > data.Close.shift(1)), 1, 0)
	data['volume_sell'] = np.where((data.Volume > data.Volume.ewm(span=5).mean()) & (data.Close < data.Close.shift(1)), 1, 0)

	last_week_data = data.tail(5).sort_values(by='Date', ascending=False)
	rsiScore = get_score(last_week_data, indicator='rsi')
	macdScore = get_score(last_week_data, indicator='macd')
	emaScore = get_score(last_week_data, indicator='ema')
	volumeScore = get_score(last_week_data, indicator='volume')
	totalScore = rsiScore + macdScore + emaScore + volumeScore
	scores = [0,0,0,0,0]
	for i in range(len(data.index.values)-5):
		df = data[i:i+5]
		rsiScore = get_score(df, indicator='rsi')
		macdScore = get_score(df, indicator='macd')
		emaScore = get_score(df, indicator='ema')
		volumeScore = get_score(df, indicator='volume')
		totalScore = rsiScore + macdScore + emaScore + volumeScore
		scores.append(totalScore)

	data['scores'] = scores
	data['scores'] = data.scores.ewm(span=5).mean()
	data.to_csv(f'output/{ticker}.csv')
	print(f"Trained {ticker}")

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
	train(ticker)