from django.urls import path
from .views import HomePage, PlaceOrder, StockDetail, requestSearch, getStockPrice
from django.contrib.auth.decorators import login_required
urlpatterns = [
	path('', login_required(HomePage.as_view()), name='home'),
	path('stock/<str:stock_name>/', login_required(StockDetail.as_view()), name='stock'),
	path('search/', requestSearch),
	path('quote/', getStockPrice),
	path('place-order/<str:stock_name>/', login_required(PlaceOrder.as_view())),
]