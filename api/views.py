from datetime import timedelta
import random
from urllib.parse import urlparse, parse_qs

from django.http import JsonResponse 
from django.utils import timezone
from django.db.models import Q

from rest_framework.decorators import api_view 

from api.models import (
    Category, Learning_Category, Learned_Word, Word, 
    Word_Repetition, Learning_Session, Answer_Attempt
)
from api.serializers import CategorySerializer


@api_view(['GET'])
def categories(request):
    return JsonResponse(
        CategorySerializer(Category.objects.all(), many=True).data,
        safe=False
    )

@api_view(['POST'])
def update_user_categories(request):
    try:
        data = request.data
        user = request.user
        category = Category.objects.get(id=data['category_id'])

        if category.owner not in [None, user.id]:
            raise Category.DoesNotExist
        
        if data['is_checked']:
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
        user = request.user

        word_id = data.get('word_id')

        if data['is_known']:
            Learned_Word.objects.create(user=user, word_id=word_id)
            return JsonResponse({'status': 'success', 'message': 'Known word added'}, status=200)
    
        Word_Repetition.objects.create(
            user=user,
            word_id=word_id,
            next_review=timezone.now() + timedelta(seconds=30)
        )

        return JsonResponse({'status': 'success', 'message': 'Word to learned added'}, status=200)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
     
    
@api_view(['GET'])
def get_new_word(request):
    try:
        user = request.user
        user_categories = Learning_Category.objects.filter(user=user).values_list('category_id', flat=True)
        
        if not user_categories:
            return JsonResponse({'status': 'error', 'message': 'No categories that user learns'}, status=200)

        excluded_words = set(
            Learned_Word.objects.filter(user=user).values_list('word_id', flat=True)
        ).union(
            Word_Repetition.objects.filter(user=user).values_list('word_id', flat=True)
        )

        new_words = Word.objects.filter(category__in=user_categories).exclude(id__in=excluded_words)

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

REPETITION_INTERVALS = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1}

@api_view(['POST'])
def send_repeat_result(request):
    try:
        data = request.data
        user = request.user
        word_id = data.get('word_id')

        repetition, _ = Word_Repetition.objects.get_or_create(
            user=user, 
            word_id=word_id
        )
        Answer_Attempt.objects.create(
            user=user,
            word_id=word_id,
            session_id=data['session_id'],
            is_correct=data['is_known']
        )

        if data['is_known']:
            if repetition.repetition_count == 5:
                repetition.delete()
                Learned_Word.objects.create(
                    user=user,
                    word_id=word_id
                )
                message = 'Word learned!'
            else:
                repetition.repetition_count += 1
                repetition.next_review = timezone.now() + timedelta(
                    minutes=REPETITION_INTERVALS.get(repetition.repetition_count, 0)
                )
                repetition.save()
                message = 'Repetition updated'
        else:
            repetition.repetition_count = max(0, repetition.repetition_count - 1)
            repetition.next_review = timezone.now() + timedelta(
                minutes=REPETITION_INTERVALS.get(repetition.repetition_count, 0)
            )
            repetition.save()
            message = 'Word difficulty increased'
                 
        return JsonResponse({'status': 'success', 'message': message}, status=200)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
     

@api_view(['GET'])
def get_test_questions(request):
    try:
        category_id = request.GET.get('category_id')
        words = list(Word.objects.filter(
            category__id=category_id
        ).values('id', 'word', 'transcription', 'translation'))

        if not words:
            return JsonResponse({'words': []})
        
        questions = []

        for word in words:
            wrong_translations = random.sample(
                [w['translation'] for w in words if w['id'] != word['id']],
                min(3, len(words) - 1)
            )

            options = [{'translation': word['translation'], 'is_correct': True}] + [
                {'translation': trans, 'is_correct': False} for trans in wrong_translations
            ]
            random.shuffle(options)

            questions.append({
             
                'id': word['id'],
                'word': word['word'],
                'transcription': word['transcription'],
                'options': options
            })
        
        return JsonResponse({'questions': questions})

    except Exception as e:
            return JsonResponse({'success': 'error','error': str(e)}, status=500)


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


LEARNING_METHODS = {
    'new_words': 'new_words',
    'repeat': 'repeat',
    'test': 'test'
}

@api_view(['POST'])
def track_session(request):
    try:
        data = request.data
        user = request.user
        
        if data['type'] == 'session_start':
            parsed_url = urlparse(data['page_url'])
            page = parsed_url.path.split('/')[-1]
            category_id = parse_qs(parsed_url.query).get('category_id', [None])[0]
            
            session = Learning_Session.objects.create(
                user=user,
                start_time=data['session_start'],
                method=LEARNING_METHODS.get(page, ''),
                category_id=category_id
            )
            return JsonResponse({
                'status': 'success', 
                'message': 'session was started', 
                'session_id': session.id
                }, status=200)
        
        elif data['type'] == 'session_end':
            Learning_Session.objects.filter(id=data['session_id']).update(
                end_time=data['session_end'],
                duration=data['duration']
            )

            return JsonResponse({'status': 'success', 'message': 'session was ended'}, status=200)
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)