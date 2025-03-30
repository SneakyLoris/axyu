from django.contrib import admin
from django.urls import path

from web.views import *

urlpatterns = [
    path('', main_view, name='main'),
    path('registration', registration_view, name='registration'),
    path('auth', auth_view, name='auth'),
    path('goods/<str:category_name>', goods_view, name='goods'),
    path('goods/<int:item_id>', good_view, name='good'),

]
