from django.urls import path
from . import views


app_name = 'buybacks'

urlpatterns = [
    path('', views.index, name='index'),
]
