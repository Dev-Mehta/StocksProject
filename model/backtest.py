import backtrader as bt
import pandas as pd
import os.path
import sys

class TestFeed(bt.feeds.PandasData):
	lines = ('scores', )
	params = (('scores', 20),)

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
			if self.scores[0] >= 12:
					self.log('BUY CREATE, %.2f' % self.dataclose[0])
					# Keep track of the created order to avoid a 2nd order
					self.order = self.buy()
		else:
			# Already in the market ... we might sell
			if len(self) >= (self.bar_executed + 5):
				if self.scores[0] <= 7 and self.scores >= 4:
					self.log('SELL CREATE, %.2f' % self.dataclose[0])
					self.order = self.sell()
				

cerebro = bt.Cerebro()
cerebro.addstrategy(TestStrategy)
modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
datapath = os.path.join(modpath, 'output\RELIANCE.csv')
data = pd.read_csv(datapath)
data.index = pd.to_datetime(data.Date)
data = TestFeed(dataname=data)
cerebro.adddata(data)
cerebro.broker.setcash(100000.0)
cerebro.broker.setcommission(commission=0.002)
cerebro.addsizer(bt.sizers.SizerFix, stake=100)
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
strats = cerebro.run()
strat = strats[0]
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
pyfoliozer = strat.analyzers.getbyname('pyfolio')
returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
ret = returns.sum() * 100
print("Returns: %.2f" % ret)