import backtrader as bt
import pandas as pd
import os.path
import sys
from tabulate import tabulate

class TestFeed(bt.feeds.PandasData):
	lines = ('scores', )
	params = (('scores', 24),)

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
				self.log(
					'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
					(order.executed.price,
					 order.executed.value,
					 order.executed.comm))

				self.buyprice = order.executed.price
				self.buycomm = order.executed.comm
			elif order.issell():
				self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
						 (order.executed.price,
						  order.executed.value,
						  order.executed.comm))
			self.bar_executed = len(self)

		elif order.status in [order.Canceled, order.Margin, order.Rejected]:
			self.log('Order Canceled/Margin/Rejected')

		# Write down: no pending order
		self.order = None
	def notify_trade(self, trade):
		if not trade.isclosed:
			return
		self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
				 (trade.pnl, trade.pnlcomm))

	def next(self):
		# Simply log the closing price of the series from the reference
		if self.order:
			return
		# Check if we are in the market
		if not self.position:
			# Not yet ... we MIGHT BUY if ...
			if self.scores[0] > 15:
					self.log('BUY CREATE, %.2f' % self.dataclose[0])
					# Keep track of the created order to avoid a 2nd order
					self.order = self.buy()
		else:
			# Already in the market ... we might sell
			if len(self) >= (self.bar_executed + 5):
				if self.scores[0] <= 7 and self.scores >= 4:
					self.log('SELL CREATE, %.2f' % self.dataclose[0])
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
			self.trades.append({'ID': trade.ref, 'Ticker': trade.data._name, 'Entry Type': dir,
				 'Buy Date': datein, 'Buy Price': pricein, 'Sell Date': dateout, 'Sell Price': priceout,
				 'Change %': round(pcntchange, 2), 'P&L': pnl, 'P&L%': round(pnlpcnt, 2),
				 'Quantity': size, 'No. of days held': barlen})
				 
cerebro = bt.Cerebro()
cerebro.addstrategy(TestStrategy)
modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
datapath = os.path.join(modpath, 'output\\TECHM.csv')
data = pd.read_csv(datapath)
data.index = pd.to_datetime(data.Date)
data = TestFeed(dataname=data)
cerebro.adddata(data)
cerebro.broker.setcash(100000.0)
cerebro.broker.setcommission(commission=0.002)
cerebro.addsizer(bt.sizers.SizerFix, stake=50)
cerebro.addanalyzer(trade_list, _name='trade_list')
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
strats = cerebro.run(tradehistory=True)
strat = strats[0]
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
trade_list = strats[0].analyzers.trade_list.get_analysis()
df = pd.DataFrame(trade_list)
df.set_index('ID', inplace=True)
df.to_csv("backtest_results.csv")