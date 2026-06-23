from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('analytics/', views.analytics_detail, name='analytics_detail'),
    path('api/forecast/', views.forecast_api, name='forecast_api'),
]
