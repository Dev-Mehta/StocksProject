from django.contrib import admin
from .models import StockBalanceSheet, Stock
# Register your models here.
admin.site.register(Stock)
admin.site.register(StockBalanceSheet)