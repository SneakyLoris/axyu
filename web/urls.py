from django.contrib import admin
from django.urls import path

from web.views import *

urlpatterns = [
    path('', main_view, name='main'),
    path('registration', registration_view, name='registration'),
    path('login', auth_view, name='login'),
    path('logout', logout_view, name='logout'),
    ##########################################
    path('stats/', stats_view, name='stats'),
    path('tests/', tests_view, name='tests'),
    path('category/<str:category_name>', add_category_view, name='category'),
    path('category/add', add_category_view, name='add_category'),
]
