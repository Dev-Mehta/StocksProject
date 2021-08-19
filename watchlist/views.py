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
		model = StockClassifier(tickers=[stock])
		result = model.train()
		print(result)
		return render(self.request,"stock_detail.html", {"stock_name":stock, "result":result[stock]})

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