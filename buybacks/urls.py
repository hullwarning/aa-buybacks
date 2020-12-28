from django.urls import path
from django.conf.urls import url
from . import views


app_name = 'buybacks'

urlpatterns = [
    path('', views.index, name='index'),
    path('manage', views.manage, name='manage'),
    path('setup', views.setup, name='setup'),
    path('program_add', views.program_add, name='program_add'),
    path('program_add_2', views.program_add_2, name='program_add_2'),
    url(r'^program/(?P<program_pk>[0-9]+)/$', views.program, name='program'),
    url(r'^program/(?P<program_pk>[0-9]+)/remove$',
        views.program_remove, name='program_remove'),
    url(r'^program/(?P<program_pk>[0-9]+)/add_item$',
        views.program_add_item, name='program_add_item'),
    url(r'^program/(?P<program_pk>[0-9]+)/add_location$',
        views.program_add_location, name='program_add_location'),
    url(r'^program/(?P<program_pk>[0-9]+)/remove_item/(?P<item_type_pk>[0-9]+)$',
        views.program_remove_item, name='program_remove_item'),
    url(r'^program/(?P<program_pk>[0-9]+)/remove_location/(?P<office_pk>[0-9]+)$',
        views.program_remove_location, name='program_remove_location'),
]