import json
from django.views.generic import TemplateView, View
from django.shortcuts import render
from django.http import JsonResponse
import requests
from model.model import StockClassifier
class HomePage(TemplateView):
	template_name = 'index.html'
	
class StockDetail(View):
	def get(self, request, *args, **kwargs):
		stock = kwargs['stock_name']
		stock = stock.upper()
		stock_data = requests.get(f"https://api.tickertape.in/external/oembed/{stock}").json()
		stock_data = stock_data['data']
		sid = stock_data['sid']
		stock_price = requests.get(f"https://quotes-api.tickertape.in/quotes?sids={sid}").json()
		stock_price = stock_price['data'][0]
		model = StockClassifier(tickers=[stock])
		result = model.train()[stock]
		print(result)
		return render(self.request,"stock_detail.html", {"stock_name":stock, "stock_data":stock_data, "stock_price":stock_price, "result":result})

def requestSearch(request):
	ticker = request.GET.get('query')
	req = requests.get(f"https://api.tickertape.in/search?text={ticker}&types=stock,etf&exchanges=NSE")
	jsreq = req.json()
	resp = jsreq['data']['stocks']
	result = {}
	res = []
	for i in resp:
		name = i['ticker']
		res.append({'ticker':i['name'] + ' - ' + i['ticker'], 'name':i['name'] + ' - ' + i['ticker'], 'url': f'/stock/{name}'})
	result['results'] = res
	return JsonResponse(result, safe=False)

def getStockPrice(request):
	ticker = request.GET.get('query')
	ticker = ticker.upper()
	stock_data = requests.get(f"https://api.tickertape.in/external/oembed/{ticker}").json()
	stock_data = stock_data['data']
	sid = stock_data['sid']
	stock_price = requests.get(f"https://quotes-api.tickertape.in/quotes?sids={sid}").json()
	stock_price = stock_price['data'][0]
	stock_price['percentageChange'] = (stock_price['change'] / stock_price['c']) * 100 
	return JsonResponse(stock_price, safe=False)

class PlaceOrder(View):
	def get(self, request, *args, **kwargs):
		stock = kwargs['stock_name']
		stock = stock.upper()
		return render(self.request,"stock_place_order.html", {"stock_name":stock})	
