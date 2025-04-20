from django.contrib import admin
from django.urls import path

from web.views import *

urlpatterns = [
    path('', main_view, name='main'),
    path('registration', registration_view, name='registration'),
    path('login', auth_view, name='login'),
    path('logout', logout_view, name='logout'),
    ##########################################
    path('stats', stats_view, name='stats'),
    path('learning', learning_view, name='learning'),
    path('learning/new_words', learning_new_words_view, name='learning_new_words'),
    path('learning/repeat', learning_repeat_view, name='learning_repeat'),
    path('learning/tests', learning_tests_view, name='learning_tests'),
    ##########################################
    path('categories', categories_view, name='categories'),
    path('categories/<str:category_name>', categories_wordlist_view, name='categories_wordlist'),

    path('category/add', add_category_view, name='add_category'),
    path('category/remove', remove_category_view, name='remove_category'),
]
