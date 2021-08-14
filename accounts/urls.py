from django.urls import path
from django.contrib.auth import views as auth_views
from .views import signup
urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('register/', signup, name='register'),
]