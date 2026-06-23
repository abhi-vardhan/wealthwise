from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('add-reminder/', views.add_bill_reminder, name='add_bill_reminder'),
    path('delete-reminder/<int:pk>/', views.delete_bill_reminder, name='delete_bill_reminder'),
    path('unread-count/', views.unread_count, name='unread_count'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
]
