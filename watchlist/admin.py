from django.contrib import admin
from .models import PendingTrades, Stock, WatchList
# Register your models here.
admin.site.register(Stock)
admin.site.register(WatchList)
admin.site.register(PendingTrades)