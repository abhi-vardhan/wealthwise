from django.urls import path
from . import views

urlpatterns = [
    path('', views.voice_log, name='voice_log'),
    path('process/', views.process_voice, name='process_voice'),
    path('save/', views.save_voice_transaction, name='save_voice_transaction'),
]
