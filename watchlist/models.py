from django.db import models
from django.contrib.auth.models import User
from numpy import mod

class WatchList(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	stocks = models.ManyToManyField('Stock')

class Stock(models.Model):
	name = models.CharField(max_length=200)

	def __str__(self) -> str:
		return self.name