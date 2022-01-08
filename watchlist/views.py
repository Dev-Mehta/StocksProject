from django.contrib.auth.models import User
from watchlist.models import Stock, WatchList
from django.views.generic import TemplateView, View
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import requests, json
import pandas as pd
from model.model import StockClassifier
class HomePage(TemplateView):
	template_name = 'index.html'

	def get_context_data(self, *args,**kwargs):
		context = super().get_context_data(**kwargs)
		watchlist = WatchList.objects.filter(user=User.objects.get(username=self.request.user.username))
		data = []
		if watchlist.exists():
			context['watchlist'] = watchlist[0]
			watchlist = watchlist[0]
			for stock in watchlist.stocks.all():
				stock_data = requests.get(f"https://api.tickertape.in/external/oembed/{stock}").json()
				stock_data = stock_data['data']
				sid = stock_data['sid']
				stock_price = requests.get(f"https://quotes-api.tickertape.in/quotes?sids={sid}").json()
				stock_price = stock_price['data'][0]
				stock_price['percentageChange'] = (stock_price['change'] / stock_price['c']) * 100
				data.append({'stock':stock, 'price':stock_price})
			context['data'] = data
		return context
	
class StockDetail(View):
	def get(self, request, *args, **kwargs):
		stock = kwargs['stock_name']
		stock = stock.upper()
		try:
			stock_data = requests.get(f"https://api.tickertape.in/external/oembed/{stock}").json()
			stock_data = stock_data['data']
			sid = stock_data['sid']
			stock_price = requests.get(f"https://quotes-api.tickertape.in/quotes?sids={sid}").json()
			stock_price = stock_price['data'][0]
			model = StockClassifier(ticker=stock)
			result = model.train()
			backtest_result = pd.DataFrame(result['backtest_results'])
			pnl = backtest_result['pnl']
			accuracy = (pnl[pnl > 0].count() / pnl.count()) * 100
			records = result['backtest_results']
			buying_factors = result['buying_factors']
			selling_factors = result['selling_factors']
			buy_count, sell_count = sum(buying_factors.values()), sum(selling_factors.values())
			neutral_count = 4 - buy_count - sell_count
			strong_buy = buy_count == 4
			good_buy = buy_count >= 2 
			neutral_buy = buy_count < 2 and sell_count < 2
			strong_sell = sell_count == 4
			good_sell = sell_count >= 2
			message = ""
			if good_buy:
				message = "Buy"
			if strong_buy:
				message = "Strong Buy"
			if neutral_buy:
				message = "Neutral"
			if good_sell:
				message = "Sell"
			if strong_sell:
				message = "Strong Sell"
			context = {"stock_name":stock,
			"stock_data":stock_data,
			"stock_price":stock_price,
			"result":result,
			"message":message,
			"buy_count":buy_count,
			"sell_count":sell_count,
			"neutral_count":neutral_count,
			"buying_factors":buying_factors,
			"selling_factors":selling_factors,
			"price":result['price'],
			"stock_exists":True,
			"backtest_start":result['backtest_start'],
			"backtest_end":result['backtest_end'],
			"backtest_result":backtest_result,
			"backtest_accuracy":accuracy,
			"trade_list":records,
			}
			watchlist = WatchList.objects.filter(user=User.objects.get(username=request.user.username))
			if watchlist.exists():
				watchlist = watchlist[0]
				if watchlist.stocks.filter(name=stock).exists():
					context['stockAdded'] = True
				else:
					context['stockAdded'] = False
			return render(self.request,"stock_detail.html", context)
		except TypeError:
			stock_name = kwargs['stock_name']
			return render(self.request, "stock_detail.html", {"stock_name":stock_name})
		

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

class AddToWatchlist(View):
	@method_decorator(csrf_exempt)
	def dispatch(self, request, *args, **kwargs) :
		return super().dispatch(request, *args, **kwargs)
	def post(self, request, *args, **kwargs):
		if not self.request.user.is_authenticated:
			return JsonResponse({"error":"User not logged in", "success":False})
		stock = self.request.POST.get('stock')
		stock = stock.upper()
		user = User.objects.get(username=self.request.user.username)
		stockObj, sCreated = Stock.objects.get_or_create(name=stock)
		watchlist, created = WatchList.objects.get_or_create(user=user)
		if sCreated:
			stockObj.save()
			watchlist.stocks.add(stockObj)
			watchlist.save()
			return JsonResponse({"success":True, "message":f""})
		watchlist.save()
		message = "Added"
		if WatchList.objects.filter(user=user, stocks=stockObj).exists():
			watchlist.stocks.remove(stockObj)
			message = "Removed"
		else:
			watchlist.stocks.add(stockObj)
			watchlist.save()
		return JsonResponse({"success":True, "message":message})
