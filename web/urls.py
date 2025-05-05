from django.contrib import admin
from django.urls import path

from web.views import *

urlpatterns = [
    path('', main_view, name='main'),
    path('registration', registration_view, name='registration'),
    path('login/', auth_view, name='login'),
    path('logout', logout_view, name='logout'),
    path('stats', stats_view, name='stats'),
    ##########################################
    path('learning', learning_view, name='learning'),
    path('learning/new_words', learning_new_words_view, name='learning_new_words'),
    path('learning/repeat', learning_repeat_view, name='learning_repeat'),
    path('learning/tests', learning_tests_view, name='learning_tests'),
    path('learning/test', category_test, name='category_test'),
    ##########################################
    path('categories', categories_view, name='categories'),
    path('categories/<str:category_name>', categories_wordlist_view, name='categories_wordlist'),
    path('category/add', add_category_view, name='add_category'),
    path('category/remove/<int:category_id>/', remove_category_view, name='remove_category'),
    path('category/edit/<int:category_id>', edit_category_view, name='edit_category'),
    path('feedback/', feedback_view, name='feedback'),
    path('category/reset_progress/<int:category_id>/', reset_category_progress_view, name='reset_category_progress'),
    path('category/add_word/<int:category_id>/', add_word_to_category_view, name='add_word_to_category'),
    path('words/<int:word_id>/start_learning/', word_start_learning, name='word_start_learning'),
    path('words/<int:word_id>/mark_known/', word_mark_known, name='word_mark_known'),
    path('words/<int:word_id>/reset_progress/', word_reset_progress, name='word_reset_progress'),
    path('words/<int:word_id>/edit/', word_edit, name='word_edit'),
    path('words/<int:word_id>/delete/', word_delete, name='word_delete'),
]
