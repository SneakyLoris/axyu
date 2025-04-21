from django.urls import path

from api import views


urlpatterns = [
    path('categories', views.categories, name = 'api_categories')
]