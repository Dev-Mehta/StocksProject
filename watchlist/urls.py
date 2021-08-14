from django.urls import path
from .views import HomePage, StockDetail
from django.contrib.auth.decorators import login_required
urlpatterns = [
	path('', login_required(HomePage.as_view()), name='home'),
	path('stock/<str:stock_name>/', login_required(StockDetail.as_view()), name='stock'),
]