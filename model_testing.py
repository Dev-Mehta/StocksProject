import os, sys, django
sys.path.append("D:\Projects\StocksProject")
sys.path.append("D:\Projects\StockBlog")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stockmarket.settings")
django.setup()

from model.model import StockClassifier

m = StockClassifier('RELIANCE')
result, df, initial_date = m.train()

# tl = df['trade_list']
if result['buy_call']:
    print("BUY CALL TODAY UPADO UPADO")
else:
    print("HAMNA KHAMO")
# profit_list = [{'date':i['sell_date'].year, 'profit':10000}]
# for i in tl:
#     profit_list.append({'date':i['sell_date'].year, 'profit':i['account_value']})
# print(profit_list)
