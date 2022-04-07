from django.contrib.auth.models import User
from watchlist.models import Stock, WatchList
from django.views.generic import TemplateView, View
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import requests, json
import pandas as pd
from model.model import StockModel, StockScreener
from io import BytesIO
from django.http import StreamingHttpResponse
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
			# stock_data, stock_price = None, None
			model = StockModel(ticker=stock)
			result, df, initial_year = model.train()
			backtest_result = pd.DataFrame(result['backtest_results'])
			pnl = backtest_result['pnl']
			profit = pnl.sum()
			avg_pl = profit / len(pnl)
			avg_profit = pnl[pnl > 0].mean()
			avg_loss = pnl[pnl < 0].mean()
			max_profit = pnl.max()
			max_loss = pnl.min()
			ending_value = result['ending_value']
			print(format_indian(ending_value))
			returns = ((ending_value - 500000) / 500000) * 100
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
			tl = df['trade_list']
			profit_list = [{'date':initial_year, 'profit':500000}]
			for i in tl:
				profit_list.append({'date':i['sell_date'], 'profit':i['account_value']})
			last_order = result['last_order']
			if last_order != None:
				last_order['pnl'] = (stock_price['price'] - last_order['price']) * last_order['size']
			
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
			"backtest_profit": profit,
			"trade_list":records,
			"total_trades":len(records),
			"avg_pl":avg_pl,
			"avg_profit":avg_profit,
			"avg_loss":avg_loss,
			"max_profit":max_profit,
			"max_loss":max_loss,
			"ending_value": format_indian(ending_value),
			"returns":returns,
			"score":result['score'],
			"profit_list":profit_list,
			"buy_today":result['buy_call'],
			"sell_today":result['sell_call'],
			"last_order":last_order,
			}
			watchlist = WatchList.objects.filter(user=User.objects.get(username=request.user.username))
			if watchlist.exists():
				watchlist = watchlist[0]
				if watchlist.stocks.filter(name=stock).exists():
					context['stockAdded'] = True
				else:
					context['stockAdded'] = False
			return render(self.request,"stock_detail.html", context)
		# except IndexError:
		# 	stock_name = kwargs['stock_name']
		# 	return render(self.request, "stock_detail.html", {"stock_name":stock_name})
		except TypeError:
			stock_name = kwargs['stock_name']
			return render(self.request, "stock_detail.html", {"stock_name":stock_name})
		

def requestSearch(request):
	ticker = request.GET.get('query')
	url = f"https://api.tickertape.in/search?text={ticker}&types=stock,brands,index,etf,mutualfund&exchanges=NSE"
	req = requests.get(url)
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

class Nifty100Screener(View):
	def get(self, request, *args, **kwargs):
		df = pd.read_csv('https://www1.nseindia.com/content/indices/ind_nifty100list.csv/')
		tickers = df.Symbol.to_numpy()
		tickers.sort()
		buy_calls = []
		for i in range(len(tickers)):
			try:
				buy_call = StockScreener(tickers[i]).train()['buy_call']
				if buy_call:
					buy_calls.append(tickers[i])
			except:
				pass
		return render(self.request,"nifty_screener.html", {"buy_calls":buy_calls})

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
def format_indian(t):
	dic = {
		4:'Thousand',
		5:'Lakh',
		6:'Lakh',
		7:'Crore',
		8:'Crore',
		9:'Arab'
	}
	y = 10
	len_of_number = len(str(t))
	save = t
	z=y
	while(t!=0):
		t=int(t/y)
		z*=10

	zeros = len(str(z)) - 3
	if zeros>3:
		if zeros%2!=0:
			string = str(save/(z/100))[0:4]+" "+dic[zeros]
		else:   
			string = str(save/(z/1000))[0:4]+" "+dic[zeros]
		return string
	return str(save)
	
def download(request):
	ticker = request.GET.get('ticker')
	if ticker != None:
		sio = BytesIO()
		s = Stock.objects.filter(name=ticker)
		if s.exists():
			s = s[0]
			data = json.loads(s.backtest_result)
			print(data)
			PandasDataFrame = pd.DataFrame()
			PandasWriter = pd.ExcelWriter(sio, engine='xlsxwriter')
			PandasDataFrame.to_excel(PandasWriter, sheet_name=f'{ticker}_results.csv')
			PandasWriter.save()
			filename = f'{ticker}_results.csv'
			sio.seek(0)
			workbook = sio.getvalue()

			response = StreamingHttpResponse(workbook, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
			response['Content-Disposition'] = 'attachment; filename=%s' % filename
			return response