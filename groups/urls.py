from django.urls import path
from . import views

urlpatterns = [
    path('', views.group_list, name='group_list'),
    path('create/', views.create_group, name='create_group'),
    path('<int:pk>/', views.group_detail, name='group_detail'),
    path('<int:pk>/add-expense/', views.add_group_expense, name='add_group_expense'),
    path('settle/<int:split_pk>/', views.settle_split, name='settle_split'),
]
