from django.urls import path
from . import views

urlpatterns = [
    path('', views.transaction_list, name='transaction_list'),
    path('add/', views.add_transaction, name='add_transaction'),
    path('<int:pk>/edit/', views.edit_transaction, name='edit_transaction'),
    path('<int:pk>/delete/', views.delete_transaction, name='delete_transaction'),
    path('categories/', views.categories_view, name='categories'),
    path('quick-add/', views.quick_add_ajax, name='quick_add_ajax'),
]
