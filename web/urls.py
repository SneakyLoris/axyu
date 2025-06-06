from django.urls import path

from web.views import *

urlpatterns = [
    path('', main_view, name='main'),
    path('registration', registration_view, name='registration'),
    path('login/', auth_view, name='login'),
    path('logout', logout_view, name='logout'),
    path('stats', stats_view, name='stats'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', profile_edit_view, name='profile_edit'),
    path('profile/delete/', profile_delete_view, name='profile_delete'),
    ##########################################
    path('learning', learning_view, name='learning'),
    path('learning/new_words', learning_new_words_view, name='learning_new_words'),
    path('learning/repeat', learning_repeat_view, name='learning_repeat'),
    path('learning/tests', learning_tests_view, name='learning_tests'),
    path('learning/test', category_test, name='category_test'),
    ##########################################
    path('categories', categories_view, name='categories'),
    path('categories/<int:category_id>', categories_wordlist_view, name='categories_wordlist'),
    path('category/add/', add_category_view, name='add_category'),
    path('category/remove/<int:category_id>/', remove_category_view, name='remove_category'),
    path('category/edit/<int:category_id>/', edit_category_view, name='edit_category'),
    path('feedback/', feedback_view, name='feedback'),
    path('feedback/list/', feedback_list_view, name='feedback_list'),
    path('feedback/edit/<int:pk>/', feedback_edit_view, name='feedback_edit'),
    path('feedback/delete/<int:pk>/', feedback_delete_view, name='feedback_delete'),
    path('category/reset_progress/<int:category_id>/', reset_category_progress_view, name='reset_category_progress'),
    path('category/add_word/<int:category_id>/', add_word_to_category_view, name='add_word_to_category'),
    path('words/start_learning/<int:word_id>/', word_start_learning, name='word_start_learning'),
    path('words/mark_known/<int:word_id>/', word_mark_known, name='word_mark_known'),
    path('words/reset_progress/<int:word_id>/', word_reset_progress, name='word_reset_progress'),
    path('words/edit/<int:category_id>/<int:word_id>/', word_edit, name='word_edit'),
    path('words/delete/<int:category_id>/<int:word_id>/', word_delete, name='word_delete'),
    path('update_user_categories/', update_user_categories, name = 'update_user_categories'),
    path('learning/new_word_send_result/', new_word_send_result, name = 'new_word_send_result'),
    path('learning/get_new_word/', get_new_word, name = 'get_new_word'),
    path('learning/get_word_repeat/', get_word_repeat, name = 'get_word_repeat'),
    path('learning/send_repeat_result/', send_repeat_result, name = 'send_repeat_result'),
    path('learning/get_test_questions/', get_test_questions, name = 'get_test_questions'),
    path('search_words/', search_words, name='search_words'),
    path('track_session/', track_session, name='track_session')
]