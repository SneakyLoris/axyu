from django.http import HttpResponse, JsonResponse 
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view 

from api.models import Category, Learning_Category
from api.serializers import CategorySerializer


@csrf_exempt
@api_view(['GET'])
def categories(request):
    categories = Category.objects.all();
    serializer = CategorySerializer(categories, many=True)
    return JsonResponse(serializer.data, safe=False)


@csrf_exempt
@api_view(['POST'])
def update_user_categories(request):
    try:
        data = request.data

        category_id = data.get('category_id')
        is_checked = data.get('is_checked')

        user = request.user
        category = Category.objects.get(id=category_id)

        if category.owner not in [None, user.id]:
            raise Category.DoesNotExist
        
        if is_checked:
            Learning_Category.objects.get_or_create(user=user, category=category)
            message = f"Category '{category.name}' added"
        else:
            Learning_Category.objects.filter(user=user, category=category).delete()
            message = f"Category '{category.name}' deleted"
            
        return JsonResponse({'status': 'success', 'message': message}, status=200)
    
    except Category.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Category not found'}, status=404)
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)