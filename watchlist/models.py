from django.db import models
from django.contrib.auth.models import User
from numpy import mod
from pandas.core.algorithms import mode

class WatchList(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	stocks = models.ManyToManyField('Stock')
	def __str__(self) -> str:
		return self.user.username

class Stock(models.Model):
	name = models.CharField(max_length=200)
	backtest_result = models.TextField(blank=True, null=True)

	def __str__(self) -> str:
		return self.name

class PendingTrades(models.Model):
	name = models.CharField(max_length=200)
	entry = models.FloatField()
	sl = models.FloatField()
	target = models.FloatField()
	entry_date = models.DateField()
	executed = models.BooleanField(default=False)
	def __str__(self) -> str:
		return self.name