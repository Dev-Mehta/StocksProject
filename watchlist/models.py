from django.db import models
from django.contrib.auth.models import User
from numpy import mod

class WatchList(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	stocks = models.TextField()

class Stock(models.Model):
	name = models.CharField(max_length=200)
	sector = models.CharField(max_length=200)
	summary = models.TextField()
	currentPrice = models.FloatField()

	def __str__(self) -> str:
		return self.name

class StockBalanceSheet(models.Model):
	stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
	# timestamp
	date = models.DateField()
	# current assets
	currentAssets = models.FloatField()
	# under current assets
	cash = models.FloatField()
	shortTermInvestments = models.FloatField()
	totalReceivables = models.FloatField()
	totalInventory = models.FloatField()
	# other assets
	otherCurrentAssets = models.FloatField()
	nonCurrentAssets = models.FloatField()
	longTermInvestments = models.FloatField()
	# total assets
	totalAssets = models.FloatField()
	# liabilities
	accountsPayable = models.FloatField()
	# other liabilities
	otherCurrentLiabilities = models.FloatField()
	totalLongTermDebt = models.FloatField()
	otherLiabilities = models.FloatField()
	# total liabilites
	totalLiabilities = models.FloatField()
	commonStock = models.FloatField()
	capitalSurplus = models.FloatField()
	minorityInterest = models.FloatField()
	totalEquity = models.FloatField()

	def __str__(self) -> str:
		return str(self.stock) + str(self.date)