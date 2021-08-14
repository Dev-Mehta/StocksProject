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
	bookValue = models.FloatField()
	high = models.FloatField()
	low = models.FloatField()