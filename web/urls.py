from django.contrib import admin
from django.urls import path

from web.views import *

urlpatterns = [
    path('', main_view, name='main'),
    path('registration', registration_view, name='registration'),
    path('login', auth_view, name='login'),
    path('logout', logout_view, name='logout'),
    path('goods/<str:category_name>', goods_view, name='goods'),
    path('goods/<int:item_id>', good_view, name='good'),
    path('stats/', good_view, name='stats'),  # ТЕСТОВЫЙ РЕЖИМ!!!!
    path('tests/', good_view, name='tests'),  # ТЕСТОВЫЙ РЕЖИМ!!!!
    path('categories/add', good_view, name='add_category'),  # ТЕСТОВЫЙ РЕЖИМ!!!!
]
