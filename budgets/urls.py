from django.urls import path
from . import views

urlpatterns = [
    path('', views.budget_list, name='budget_list'),
    path('create/', views.create_budget, name='create_budget'),
    path('<int:pk>/', views.budget_detail, name='budget_detail'),
    path('<int:pk>/delete/', views.delete_budget, name='delete_budget'),
]
