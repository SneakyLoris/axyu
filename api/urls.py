from django.urls import path

from api import views


urlpatterns = [
    path('categories/', views.categories, name = 'api_categories'),
    path('update_user_categories/', views.update_user_categories, name = 'update_user_categories'),
    path('learning/new_word_send_result', views.new_word_send_result, name = 'new_word_send_result'),
    path('learning/get_new_word', views.get_new_word, name = 'get_new_word')
]