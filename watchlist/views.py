import json
from django.views.generic import TemplateView, View
from django.shortcuts import render
import yfinance as yf
from .models import Stock, StockBalanceSheet
class HomePage(TemplateView):
	template_name = 'index.html'
	
class StockDetail(View):
	def get(self, request, *args, **kwargs):
		stock = kwargs['stock_name']
		stock = stock.upper()
		s = Stock.objects.filter(name=stock)
		if not s.exists():
			stock_data = yf.Ticker(stock + '.NS')
			stock_financials = stock_data.get_balance_sheet(as_dict=True)
			stock_info = stock_data.info
			s = Stock()
			s.name = stock
			s.sector = stock_info['sector']
			s.summary = stock_info['longBusinessSummary']
			s.currentPrice = stock_info['regularMarketPrice']
			s.save()
			for key in stock_financials.keys():
				financial_year_data = stock_financials[key]
				sb = StockBalanceSheet(stock=s)
				sb.accountsPayable = financial_year_data['Accounts Payable'] / 10000000
				sb.cash = financial_year_data['Cash'] / 10000000
				sb.capitalSurplus = financial_year_data['Capital Surplus'] / 10000000
				sb.commonStock = financial_year_data['Common Stock'] / 10000000
				sb.currentAssets = financial_year_data['Total Current Assets'] / 10000000
				sb.date = key.date()
				sb.longTermInvestments = financial_year_data['Long Term Investments'] / 10000000
				sb.nonCurrentAssets = ( financial_year_data['Total Current Assets'] - financial_year_data['Other Current Assets'] )/ 10000000
				sb.minorityInterest = financial_year_data['Minority Interest'] / 10000000
				sb.otherCurrentAssets = financial_year_data['Other Current Assets'] / 10000000
				sb.otherLiabilities = financial_year_data['Other Liab'] / 10000000
				sb.otherCurrentLiabilites = financial_year_data['Other Current Liab'] / 10000000
				sb.shortTermInvestments = financial_year_data['Short Term Investments'] / 10000000 or 0.0
				sb.totalAssets = financial_year_data['Total Assets'] / 10000000
				sb.totalEquity = financial_year_data['Total Stockholder Equity'] / 10000000
				sb.totalInventory = financial_year_data['Inventory'] / 10000000
				sb.totalLiabilites = financial_year_data['Total Liab'] / 10000000
				sb.totalLongTermDebt = financial_year_data['Long Term Debt'] / 10000000
				sb.totalReceivables = financial_year_data['Net Receivables'] / 10000000
				sb.save()
		s = Stock.objects.get(name=stock)
		sb = StockBalanceSheet.objects.filter(stock=s).order_by('date')
		return render(self.request,"stock_detail.html", {"stock_data":s, "balance_sheet":sb})