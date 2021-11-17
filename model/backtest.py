import os, sys, django
sys.path.append("D:\Projects\StocksProject")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stockmarket.settings")
django.setup()
from model import StockClassifier
import pandas as pd
from watchlist.models import PendingTrades
df = pd.read_csv("data/RELIANCE.csv")
s = StockClassifier(["RELIANCE"], dataset=df)
for i in range(len(df) - 100):
	data = df[i:i+100]
	s = StockClassifier(['RELIANCE'], dataset=data)
	s.train()
	result = s.trainedResult['RELIANCE']
	if 'bullish_engulfing' in result.keys():
		be = result['bullish_engulfing']
		entry, sl, target = be['entry'], be['stoploss'], be['target']
		name = f"RELIANCE@{entry}"
		pe_query = PendingTrades.objects.filter(name=name).exists()
		if not pe_query:
			pe = PendingTrades(name=name)
			pe.entry = entry
			pe.sl = sl
			pe.target = target
			pe.entry_date = be['record_date_bullish_engulfed']
			pe.save()
			print("Trade Created...", name)