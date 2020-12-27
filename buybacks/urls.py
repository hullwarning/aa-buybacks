from django.urls import path
from . import views


app_name = 'buybacks'

urlpatterns = [
    path('', views.index, name='index'),
    path('manage', views.manage, name='manage'),
    path('setup', views.setup, name='setup'),
]
