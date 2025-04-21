from django.urls import path

from api import views


urlpatterns = [
    path('categories/', views.categories, name = 'api_categories'),
    path('update_user_categories/', views.update_user_categories, name = 'update_user_categories')
]