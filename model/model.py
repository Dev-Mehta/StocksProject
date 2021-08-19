import datetime
import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
import math

class StockClassifier:
	start_date = str((datetime.datetime.now() - datetime.timedelta(days=365)).date()) 
	end_date = str(datetime.datetime.today().date())
	trainedResult = []
	isTrained = False
	tickers = []
	def __init__(self, tickers, *args, **kwargs) -> None:
		self.tickers = tickers
	
	def is_bullish_candlestick(self, candle):
		return candle['Close'] > candle['Open']

	def is_bearish_candlestick(self, candle):
		return candle['Close'] < candle['Open']

	def is_bullish_engulfing(self, candles):
		ticker_result = []
		for i in range(1,len(candles)):
			current_day = candles.iloc[i]
			previous_day = candles.iloc[i-1]
			if self.is_bearish_candlestick(previous_day)\
			and current_day['Close'] > previous_day['Open']\
			and current_day['Open'] < previous_day['Close']:
				ticker_result.append({"current":current_day.Date, "previous":previous_day.Date})
		if len(ticker_result) > 0:
			return ticker_result
		return None


	def is_bearish_engulfing(self,candles):
		ticker_result = []
		for i in range(1,len(candles)):
			current_day = candles.iloc[i]
			previous_day = candles.iloc[i-1]
			if self.is_bullish_candlestick(previous_day)\
			and current_day['Open'] > previous_day['Close']\
			and current_day['Close'] < previous_day['Open']:
				ticker_result.append({"current":current_day.Date, "previous":previous_day.Date})
		if len(ticker_result) > 0:
			return ticker_result
		return None

	def percentage(self, value, n):
		return value + ( value * n / 100)
	def train(self):
		self.isTrained = True
		result = {}
		for ticker in self.tickers:
			ticker = ticker.upper()
			ticker_result = {}
			data = yf.download(ticker + '.NS', self.start_date, self.end_date)
			data.Date = pd.to_datetime(data.Date)
			data.index = data.Date
			high_low = data['High'] - data['Low']
			high_close = np.abs(data['High'] - data['Close'].shift())
			low_close = np.abs(data['Low'] - data['Close'].shift())
			ranges = pd.concat([high_low, high_close, low_close], axis=1)
			true_range = np.max(ranges, axis=1)
			atr = true_range.rolling(14).sum()/14
			# Calculating Moving Averages
			days12 = data.Close.ewm(span=12, adjust=False).mean()
			days26 = data.Close.ewm(span=26, adjust=False).mean()
			days5 = data.Close.ewm(span=5, adjust=False).mean()
			days13 = data.Close.ewm(span=13, adjust=False).mean()
			"""
			Calculating MACD
			"""
			macd = days12 - days26
			macd_smoothing = macd.ewm(span=9, adjust=False).mean()
			
			"""
			Calculating RSI
			"""
			close = data.Close
			delta = close.diff()
			delta = delta[1:]
			up,down = delta.clip(lower=0), delta.clip(upper=0)
			roll_up = up.ewm(span=14).mean()
			roll_down = down.abs().ewm(span=14).mean()
			rsi = roll_up / roll_down
			rsi = 100.0 - (100.0 / (1.0 + rsi))
			"""
			Fetching Volume of Last 5 days
			"""
			volume = data.Volume.tail(5)
			"""
			Here last_5_days_data is a list consisting these values by their index
			0: MACD
			1: MACD_SMOOTHING
			2: RSI
			3: VOLUME
			4: 5 Day EMA
			5: 26 Day EMA
			for Last 5 Days Data
			"""
			last_5_days_data = [macd.tail(5), macd_smoothing.tail(5), rsi.tail(5), volume.tail(5), days5.tail(5), days26.tail(5)]
			last_5_days_data = np.array(last_5_days_data).T
			today = last_5_days_data[-1]
			buying_factors = []
			selling_factors = []
			buy, sell = 'BUY', 'SELL'
			# If macd gives buy signal
			if today[0] > today[1]:
				ticker_result['macd'] = buy
				buying_factors.append("macd")
			# if macd gives sell signal
			elif today[0] < today[1]:
				ticker_result['macd'] = sell
				selling_factors.append("macd")
			# if rsi gives buy signal
			if today[2] >= 60:
				ticker_result['rsi'] = buy
				buying_factors.append("rsi")
			# if rsi gives sell signal
			elif today[2] <= 40:
				ticker_result['rsi'] = sell
				selling_factors.append("rsi")
			# if 5 day ema gives buy signal by cutting 26 day ema from below
			if today[4] > today[5]:
				ticker_result['5demacutting26dema'] = buy
				buying_factors.append("5demacutting26dema")
			# if 5 day ema gives sell signal by cutting 26 day ema from above
			else:
				ticker_result['5demacutting26dema'] = sell
				selling_factors.append("26demacutting5dema")
			# if volume is high
			if today[3] >= volume.nlargest(2).iloc[1] or today[3] >= volume.nlargest(3).iloc[0]:
				# if volume is high with bullish candle
				if today[4] > today[5]:
					ticker_result['volume'] = buy
					buying_factors.append("volume")
				# if volume is high with bearish candle
				else:
					ticker_result['volume'] = sell
					selling_factors.append("volume")
			# get the last 5 candles
			candles = data.tail(5)
			# scan for bullish and bearish engulfing
			is_bull_en = self.is_bullish_engulfing(candles)
			is_bear_en = self.is_bearish_engulfing(candles)
			target, sl, entry = 0,0,0
			if is_bull_en != None and is_bear_en != None:
				if is_bear_en[-1]["current"] > is_bull_en[-1]["current"]:
					ticker_result['bearish_engulfing'] = {'is_bearish_engulfing':True,
					 'record_date_bearish_engulfing':is_bear_en[-1]['current'],
					  'record_date_bearish_engulfed':is_bear_en[-1]['previous']}
					selling_factors.append("bearish_engulfing")
				else:
					previous_candle = candles[candles["Date"] == is_bull_en[-1]["previous"]]
					current_candle = candles[candles["Date"] == is_bull_en[-1]["current"]]
					refactor = int(current_candle.Close.iloc[0] * 0.01)
					if previous_candle.Close.iloc[0] > current_candle.Open.iloc[0]:
						entry = current_candle.Open.iloc[0] + refactor
						sl = previous_candle.Low.iloc[0] - refactor
						if current_candle.Low.iloc[0] < previous_candle.Low.iloc[0]:
							sl = current_candle.Low.iloc[0] - refactor
						target = math.ceil(entry + ((entry - sl) * 2))
					else:
						entry = previous_candle.Close.iloc[0] + refactor
						sl = current_candle.Low.iloc[0] - refactor
						if previous_candle.Low.iloc[0] < current_candle.Low.iloc[0]:
							sl = previous_candle.Low.iloc[0] - refactor
						target = math.ceil(entry + ((entry - sl) * 2))
					
					ticker_result['bullish_engulfing'] = {'is_bullish_engulfing':True,
					 'record_date_bullish_engulfing':is_bull_en[-1]['current'],
					  'record_date_bullish_engulfed':is_bull_en[-1]['previous'],
					  'target':target, 'entry':entry, 'stoploss':sl}
					buying_factors.append("bullish_engulfing")
			else:
				if is_bull_en != None:
					previous_candle = candles[candles["Date"] == is_bull_en[-1]["previous"]]
					current_candle = candles[candles["Date"] == is_bull_en[-1]["current"]]
					refactor = int(current_candle.Close.iloc[0] * 0.01)
					if previous_candle.Close.iloc[0] > current_candle.Open.iloc[0]:
						entry = current_candle.Open.iloc[0] + refactor
						sl = previous_candle.Low.iloc[0] - refactor
						if current_candle.Low.iloc[0] < previous_candle.Low.iloc[0]:
							sl = current_candle.Low.iloc[0] - refactor
						target = math.ceil(entry + ((entry - sl) * 2))
					else:
						entry = previous_candle.Close.iloc[0] + refactor
						sl = current_candle.Low.iloc[0] - refactor
						if previous_candle.Low.iloc[0] < current_candle.Low.iloc[0]:
							sl = previous_candle.Low.iloc[0] - refactor
						target = math.ceil(entry + ((entry - sl) * 2))
					ticker_result['bullish_engulfing'] = {'is_bullish_engulfing':True,
					 'record_date_bullish_engulfing':is_bull_en[-1]['current'],
					  'record_date_bullish_engulfed':is_bull_en[-1]['previous'],
					  'target':target, 'entry':entry, 'stoploss':sl}
					buying_factors.append("bullish_engulfing")
				if is_bear_en != None:
					ticker_result['bearish_engulfing'] = {'is_bearish_engulfing':True,
					 'record_date_bearish_engulfing':is_bear_en[-1]['current'],
					  'record_date_bearish_engulfed':is_bear_en[-1]['previous']}
					selling_factors.append("bearish_engulfing")
			ticker_result['buying_factors_count'] = len(buying_factors)
			ticker_result['selling_factors_count'] = len(selling_factors)
			result[ticker] = ticker_result
		self.trainedResult = result
		return result
	
	def filterBuy(self, factors_count: int):
		result = {}
		for ticker in self.trainedResult.keys():
			stock = self.trainedResult[ticker]
			if stock['buying_factors_count'] >= factors_count:
				result[ticker] = stock
		return result

	def filterSell(self, factors_count: int):
		result = {}
		for ticker in self.trainedResult.keys():
			stock = self.trainedResult[ticker]
			if stock['selling_factors_count'] >= factors_count:
				result[ticker] = stock
		return result

	def filterStock(self, ticker: str):
		ticker = ticker.upper()
		if ticker in self.trainedResult.keys():
			return self.trainedResult[ticker]
		else:
			return {"error":"Invalid ticker - The company might be delisted or the data is not trained yet."}