from django.http import HttpResponse, JsonResponse 
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from rest_framework.decorators import api_view 

from datetime import datetime, timedelta
import random
from urllib.parse import urlparse, parse_qs

from api.models import Category, Learning_Category, Learned_Word, Word, Word_Repetition, Learning_Session, Answer_Attempt
from api.serializers import CategorySerializer


@api_view(['GET'])
def categories(request):
    categories = Category.objects.all();
    serializer = CategorySerializer(categories, many=True)
    return JsonResponse(serializer.data, safe=False)


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
    

@api_view(['POST'])
def new_word_send_result(request):
    try:
        data = request.data

        word_id = data.get('word_id')
        is_known = data.get('is_known')
        user = request.user

        message = ''

        if is_known:
            Learned_Word.objects.create(user=user, word_id=word_id)
            message = 'Known word added'
        else:
            Word_Repetition.objects.create(
                user=user,
                word_id=word_id,
                next_review=timezone.now() + timedelta(seconds=30)
            )

        return JsonResponse({'status': 'success', 'message': message}, status=200)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
     
    
@api_view(['GET'])
def get_new_word(request):
    try:
        user_categories = Learning_Category.objects.filter(user_id=request.user.id)
        user_categories_ids = user_categories.values_list('category_id', flat=True)

        if not user_categories_ids:
            return JsonResponse({'status': 'error', 'message': 'No categories that user learns'}, status=200)

        learned_words = Learned_Word.objects.filter(user=request.user)
        learned_words_ids = learned_words.values_list('word_id', flat=True)

        repeat_words = Word_Repetition.objects.filter(user=request.user)
        repeat_words_ids = repeat_words.values_list('word_id', flat=True)

        excluded_word_ids = set(learned_words_ids) | set(repeat_words_ids)

        new_words = Word.objects.filter(
            category__in=user_categories_ids
        ).exclude(
            id__in=excluded_word_ids
        )

        if not new_words.exists():
            return JsonResponse({'status': 'error', 'message': 'No new words to learn'}, status=200)

        word_obj = random.choice(new_words)
        
        return JsonResponse({
            'status': 'success',
            'id': word_obj.id,
            'word': word_obj.word,
            'translation': word_obj.translation,
            'transcription': word_obj.transcription
        })
    except Exception as e: 
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@api_view(['GET'])
def get_word_repeat(request):
    try:
        user = request.user
        now = timezone.now()

        words_to_repeat = Word_Repetition.objects.filter(
            user=user,
            next_review__lte=now
        )

        if not words_to_repeat.exists():
            return JsonResponse({
                'status': 'error', 
                'message': 'No words to repeat'}
                , status=200)
        
        words_ids = words_to_repeat.values_list('word_id', flat=True)
        words_to_repeat = Word.objects.filter(
            id__in=words_ids
        )

        word_to_repeat = random.choice(words_to_repeat)

        return JsonResponse({
            'status': 'success',
            'id': word_to_repeat.id,
            'word': word_to_repeat.word,
            'translation': word_to_repeat.translation,
            'transcription': word_to_repeat.transcription
        })

    except Exception as e: 
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@api_view(['POST'])
def send_repeat_result(request):
    try:
        data = request.data
        user = request.user

        word_id = data.get('word_id')
        is_known = data.get('is_known')
        session_id = data.get('session_id')
        print(session_id)
        message = ''
        repetition, created = Word_Repetition.objects.get_or_create(user=user, word_id=word_id)
        Answer_Attempt.objects.create(
            user=user,
            word_id=word_id,
            session_id=session_id,
            is_correct=is_known
        )

        if is_known:
            learned = False

            if not created:
                if repetition.repetition_count == 4:
                    learned = True
                elif repetition.repetition_count == 0:
                    new_interval = 1 # 1 min
                elif repetition.repetition_count == 1:
                    new_interval = 2 # 2 min
                elif repetition.repetition_count == 2:
                    new_interval = 3 # 3 min
                elif repetition.repetition_count == 3:
                    new_interval = 4 # 4 min
                    
            if learned:
                repetition.delete()
                message = 'Word learned successfully'
            else:
                repetition.repetition_count += 1
                repetition.next_review = timezone.now() + timedelta(
                    minutes=new_interval
                )
                repetition.save()
                message = 'Word repeated successfully'
        else:
            if repetition.repetition_count > 2:
                repetition.repetition_count = 2
                new_interval = 3
                repetition.next_review = timezone.now() + timedelta(minutes=new_interval)
            else:
                new_interval = repetition.repetition_count
                repetition.next_review = timezone.now() + timedelta(
                    minutes=new_interval
                )
                repetition.save()
            message = 'Word was not repeated'
                

        return JsonResponse({'status': 'success', 'message': message}, status=200)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
     

@api_view(['GET'])
def get_test_questions(request):
    try:
        category_id = request.GET.get('category_id')
        all_words = list(Word.objects.filter(
            category__id=category_id
        ).values('id', 'word', 'transcription', 'translation'))

        if not all_words:
            return JsonResponse({'words': []})
        
        questions = []

        for word in all_words:
            other_words = [w for w in all_words if w['id'] != word['id']]
            wrong_translations = random.sample(
                [w['translation'] for w in other_words],
                min(3, len(other_words))
            )

            options = [{'translation': word['translation'], 'is_correct': True}]
            options.extend({'translation': trans, 'is_correct': False} for trans in wrong_translations)
            random.shuffle(options)

            questions.append({
             
                'id': word['id'],
                'word': word['word'],
                'transcription': word['transcription'],
                'options': options
            })
        
        return JsonResponse({'questions': questions})

    except Exception as e:
            return JsonResponse({
                'success': 'error',
                'error': str(e)
            }, status=500)


@api_view(['GET'])
def search_words(request):
    query = request.GET.get('q', '').strip()

    if not query:
         return JsonResponse({'results': []})

    words = Word.objects.filter(Q(word__icontains=query) | Q(translation__icontains=query))
    results = []
    for word in words:
        for category in word.category.all():
            results.append({
                'word': word.word,
                'translation': word.translation,
                'category_name': category.name,
                'category_id': category.id
            })

    return JsonResponse({'results': results})

@api_view(['POST'])
def track_session(request):
    try:
        data = request.data
        user = request.user
        
        if data['type'] == 'session_start':
            method = ''
            page_url = data['page_url']
            parsed_url = urlparse(page_url)
            page = parsed_url.path.split('/')[-1]
            query_params = parse_qs(parsed_url.query)
            category_id = query_params.get('category_id', [None])[0]
            category = None
            if category_id != None:
                category = Category.objects.get(id=category_id)

            match page:
                case 'new_words':
                    method = 'new_words'
                case 'repeat':
                    method = 'repeat'
                case 'test':
                    method = 'test'
            new_session = Learning_Session.objects.create(
                user=user,
                start_time=data['session_start'],
                method=method,
                category=category)
            return JsonResponse({
                'status': 'success', 
                'message': 'session was started', 
                'session_id': new_session.id
                }, status=200)
        
        elif data['type'] == 'session_end':
            session_id = data['session_id']
            updated = Learning_Session.objects.filter(id=session_id).update(
                end_time=data['session_end'],
                duration=data['duration']
            )
            print(f"Updated {updated} records")
            return JsonResponse({'status': 'success', 'message': 'session was ended'}, status=200)
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)