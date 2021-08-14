from django.views.generic import TemplateView, View
from django.shortcuts import render
import yfinance as yf
from .models import Stock
class HomePage(TemplateView):
	template_name = 'index.html'
	
class StockDetail(View):
	def get(self, request, *args, **kwargs):
		stock = kwargs['stock_name']
		s = Stock.objects.filter(name=stock)
		if not s.exists():
			try:
				stock_data = yf.Ticker(stock + '.NS')
				stock_data = stock_data.info
				s = Stock()
				s.name = stock
				s.sector = stock_data['sector']
				s.summary = stock_data['longBusinessSummary']
				s.currentPrice = stock_data['regularMarketPrice']
				s.high = stock_data['dayHigh']
				s.low = stock_data['dayLow']
				s.bookValue = stock_data['bookValue']
				s.save()
			except KeyError:
				return render(request, 'stock_detail.html')
		s = Stock.objects.get(name=stock)
		return render(self.request,"stock_detail.html", {"stock_data":s})