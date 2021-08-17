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
	currentPrice = models.FloatField(blank=True,null=True,default=None)

	def __str__(self) -> str:
		return self.name

class StockBalanceSheet(models.Model):
	stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
	# timestamp
	date = models.DateField()
	# current assets
	currentAssets = models.FloatField(blank=True,null=True,default=None)
	# under current assets
	cash = models.FloatField(blank=True,null=True,default=None)
	shortTermInvestments = models.FloatField(blank=True,null=True,default=None)
	totalReceivables = models.FloatField(blank=True,null=True,default=None)
	totalInventory = models.FloatField(blank=True,null=True,default=None)
	# other assets
	otherCurrentAssets = models.FloatField(blank=True,null=True,default=None)
	nonCurrentAssets = models.FloatField(blank=True,null=True,default=None)
	longTermInvestments = models.FloatField(blank=True,null=True,default=None)
	# total assets
	totalAssets = models.FloatField(blank=True,null=True,default=None)
	# liabilities
	accountsPayable = models.FloatField(blank=True,null=True,default=None)
	# other liabilities
	otherCurrentLiabilities = models.FloatField(blank=True,null=True,default=None)
	totalLongTermDebt = models.FloatField(blank=True,null=True,default=None)
	otherLiabilities = models.FloatField(blank=True,null=True,default=None)
	# total liabilites
	totalLiabilities = models.FloatField(blank=True,null=True,default=None)
	commonStock = models.FloatField(blank=True,null=True,default=None)
	capitalSurplus = models.FloatField(blank=True,null=True,default=None)
	minorityInterest = models.FloatField(blank=True,null=True,default=None)
	totalEquity = models.FloatField(blank=True,null=True,default=None)

	def __str__(self) -> str:
		return str(self.stock) + str(self.date)