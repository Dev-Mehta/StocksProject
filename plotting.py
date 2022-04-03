import os, sys, django

sys.path.append("D:\Projects\StocksProject")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stockmarket.settings")
django.setup()
from model.model import StockModel

c = StockModel("ADANIENT")
c.train()