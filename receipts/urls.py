from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_receipt, name='upload_receipt'),
    path('<int:pk>/review/', views.review_receipt, name='review_receipt'),
]
