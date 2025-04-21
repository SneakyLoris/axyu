from django.http import HttpResponse, JsonResponse 
from django.shortcuts import render
from rest_framework.decorators import api_view 

from api.models import Category
from api.serializers import CategorySerializer


@api_view(['GET'])
def categories(request):
    categories = Category.objects.all();
    serializer = CategorySerializer(categories, many=True)
    return JsonResponse(serializer.data, safe=False)

