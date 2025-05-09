import json
import os
import random
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.db import transaction
from django.db.models import (
    Avg, Case, CharField, Count, Exists, OuterRef,
    Q, Subquery, Value, When
)
from django.db.models.functions import Coalesce, ExtractHour, TruncDate
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from psycopg2 import IntegrityError

from web.forms import (
    AddCategoryForm, AddWordForm, AuthForm, EditCategoryForm,
    EditWordForm, FeedbackForm, RegistrationForm,
)
from web.models import (
    Answer_Attempt, Category, Learned_Word, Learning_Category, 
    Learning_Session, User, Word, Word_Repetition,
)


REPETITION_INTERVALS = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1}
LEARNING_METHODS = {
    'new_words': 'new_words',
    'repeat': 'repeat',
    'test': 'test'
}

###################### Helpers ######################
def auth_required(view_func=None, redirect_to_login=True):
    """Декоратор для проверки аутентификации пользователя."""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if redirect_to_login:
                    return redirect(settings.LOGIN_URL + '?next=' + request.path)
                return JsonResponse(
                    {'status': 'error', 'message': 'Authentication required'},
                    status=403
                )
            return view_func(request, *args, **kwargs)
        return wrapper

    if view_func:
        return decorator(view_func)
    return decorator


def get_user_categories(user):
    """Получает категории, доступные пользователю."""
    return Category.objects.filter(
        Q(owner__isnull=True) | Q(owner_id=user.id)
    )
    

def get_user_selected_categories(user):
    """Получает выбранные пользователем категории для обучения."""
    return Learning_Category.objects.filter(
        user_id=user.id).values_list('category_id', flat=True)


def check_word_permission(word, user):
    """Проверяет, есть ли у пользователя доступ к слову."""
    return word.category.filter(Q(owner__isnull=True) | Q(owner=user)).exists()


def get_word_status_annotations(user):
    """Возвращает аннотации для статуса слова."""
    return {
        'status': Case(
            When(
                Exists(Learned_Word.objects.filter(word=OuterRef('pk'), user=user)),
                then=Value('learned')
            ),
            When(
                Exists(Word_Repetition.objects.filter(word=OuterRef('pk'), user=user)),
                then=Value('in_progress')
            ),
            default=Value('new'),
            output_field=CharField()
        ),
        'repetition_count': Coalesce(
            Subquery(
                Word_Repetition.objects.filter(
                    word=OuterRef('pk'),
                    user=user
                ).values('repetition_count')[:1]
            ),
            Value(0)
        )
    }


def handle_word_file_upload(user, category, word_file):
    """Обрабатывает загрузку файла со словами."""
    upload_path = os.path.join('tmp', str(user.id), f'{category.name}.txt')
    file_path = default_storage.save(upload_path, word_file)
    absolute_file_path = default_storage.path(file_path)
    
    with default_storage.open(file_path, 'wb+') as destination:
        for chunk in word_file.chunks():
            destination.write(chunk)
    
    return absolute_file_path


def get_word_progress_data(words, user):
    """Добавляет данные о прогрессе изучения слов."""
    wordlist = list(words)
    for word in wordlist:
        word.repetition_progress = min(100, word.repetition_count * 20)
    return wordlist


def generate_test_questions(words):
    """Генерирует вопросы для теста."""
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
    return questions


def handle_session_start(user, data):
    """Обрабатывает запрос на начало сессии обучения."""
    if 'page_url' not in data or 'session_start' not in data:
        return JsonResponse({
            'status': 'error',
            'message': 'Missing required fields for session start'
        }, status=400)
    
    try:
        parsed_url = urlparse(data['page_url'])
        page = parsed_url.path.split('/')[-1]
        query_params = parse_qs(parsed_url.query)
        category_id = query_params.get('category_id', [None])[0]

        method = LEARNING_METHODS.get(page)
        if not method:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid learning method'
            }, status=400)
        
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                if category.owner and category.owner != user:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No permission for this category'
                    }, status=403)
            except Category.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Category not found'
                }, status=404)
    
        session = Learning_Session.objects.create(
            user=user,
            start_time=data['session_start'],
            method=method,
            category_id=category_id
        )
        
        return JsonResponse({
            'status': 'success', 
            'message': 'session was started', 
            'session_id': session.id
        }, status=200)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to start session: {str(e)}'
        }, status=400)


def handle_session_end(user, data):
    """Обрабатывает запрос на завершение сессии обучения."""
    required_fields = ['session_id', 'session_end', 'duration']
    if not all(field in data for field in required_fields):
        return JsonResponse({
            'status': 'error',
            'message': f'Missing required fields for session end: {", ".join(required_fields)}'
        }, status=400)
    
    try:
        session = Learning_Session.objects.get(id=data['session_id'])
        if session.user != user:
            return JsonResponse({
                'status': 'error',
                'message': 'This session does not belong to you'
            }, status=403)

        session.end_time = data['session_end']
        session.duration = data['duration']
        session.save()
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Session ended successfully'
        }, status=200)

    except Learning_Session.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Session not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to end session: {str(e)}'
        }, status=400)


###################### Views ######################
def main_view(request):
    return render(request, "web/main.html")


def registration_view(request):
    form = RegistrationForm()
    is_success = False
    if request.method == "POST":
        form = RegistrationForm(data=request.POST)
        if form.is_valid():
            user = User(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'])
            user.set_password(form.cleaned_data["password"])
            user.save()
            is_success = True

    return render(request, "web/registration.html", {
        "form": form,
        "is_success": is_success,
    })


def auth_view(request):
    form = AuthForm()

    if request.method == "POST":
        form = AuthForm(data=request.POST)
        if form.is_valid():
            user = authenticate(**form.cleaned_data)
            if user is None or not user.is_active:
                form.add_error(None, "Введены неверные данные")
            else:
                login(request, user)
                return redirect("main")

    return render(request, "web/auth.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("main")


@auth_required
def learning_view(request):
    return render(request, "web/learning.html")


@auth_required
def learning_new_words_view(request):
    return render(request, "web/new_words.html")


@auth_required
def learning_repeat_view(request):
    return render(request, "web/repeat_words.html")


@auth_required
def learning_tests_view(request):
    categories = get_user_categories(request.user)
    user_selected_categories = get_user_selected_categories(request.user)

    return render(request, "web/select_test.html", {
        "categories": categories,
        "user_selected_categories": user_selected_categories
    })


def categories_view(request):
    categories = get_user_categories(request.user)
    user_selected_categories = get_user_selected_categories(request.user)

    return render(request, "web/categories.html", {
        "categories": categories,
        "user_selected_categories": user_selected_categories
    })


@auth_required
def category_test(request):
    category_id = request.GET.get('category_id')

    if not category_id:
        raise Http404("Не указан ID категории")

    try:
        category = get_object_or_404(Category, id=category_id)
        if category.owner not in [None, request.user]:
            raise PermissionDenied("Нет доступа к этой категории")   
    except ValueError:
        raise Http404("Пустой ID категории")

    return render(request, "web/tests.html", {"category": category})


def categories_wordlist_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    user = request.user if request.user.is_authenticated else None

    if category.owner not in [None, user]:
        raise PermissionDenied("Нет доступа к этой категории")

    words = Word.objects.filter(category=category)

    if user:
        wordlist = words.annotate(**get_word_status_annotations(user)).distinct()
        wordlist = get_word_progress_data(wordlist, user)
    else:
        wordlist = words.annotate(
            status=Value('new', output_field=CharField()),
            repetition_count=Value(0),
            repetition_progress=Value(0)
        ).distinct()

    return render(request, "web/category_contains.html", {
        "wordlist": wordlist,
        "category": category,
        "highlight_word": request.GET.get('highlight', ''),
    })


@auth_required
def remove_category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id, owner=request.user)
    upload_path = os.path.join('tmp', str(request.user.id), f'{category.name}.txt')
    try:
        if default_storage.exists(upload_path):
            default_storage.delete(upload_path)
    except Exception:
        pass

    category.delete()
    return redirect('categories')


def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Спасибо за ваше сообщение! Мы свяжемся с вами в ближайшее время.')
            return redirect('feedback')
    else:
        form = FeedbackForm()

    return render(request, 'web/feedback.html', {'form': form})


@auth_required
def add_category_view(request):
    if request.method == 'POST':
        form = AddCategoryForm(request.POST, request.FILES, user=request.user)
        if not form.is_valid():
            return render(request, 'web/add_category.html', {'form': form}, status=400)

        category = form.save(commit=False)
        category.owner = request.user
        category.save()

        word_file = request.FILES.get('word_file')
        if not word_file:
            return render(request, 'web/add_category.html', {
                'form': form,
                'error': 'Файл со словами обязателен'
            }, status=400)

        try:
            absolute_file_path = handle_word_file_upload(request.user, category, word_file)
            call_command(
                'load_words',
                dir_path=os.path.dirname(absolute_file_path),
                user_name=request.user.username,
                verbosity=0
            )
        except Exception:
            upload_path = os.path.join('tmp', str(request.user.id), f'{category.name}.txt')
            if default_storage.exists(upload_path):
                default_storage.delete(upload_path)
            return render(request, 'web/add_category.html', {
                'form': form,
                'error': 'Ошибка при загрузке слов. Проверьте формат файла.'
            }, status=400)

        return redirect('categories')
    
    form = AddCategoryForm()
    return render(request, 'web/add_category.html', {'form': form})


@auth_required
def edit_category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id, owner=request.user)

    if request.method == 'POST':
        form = EditCategoryForm(request.POST, request.FILES, instance=category, user=request.user)
        if not form.is_valid():
            return render(request, 'web/edit_category.html', {
                'form': form,
                'category': category
            }, status=400)
        
        form.save()
        return redirect('categories_wordlist', category_id=category.id)
    
    form = EditCategoryForm(instance=category, user=request.user)
    return render(request, 'web/edit_category.html', {
        'form': form,
        'category': category
    })


def stats_view(request):
    user = request.user

    total_learned_words = len(Learned_Word.objects.filter(user=user))
    total_repetitions = len(Answer_Attempt.objects.filter(user=user))
    avg_time_of_tests = Learning_Session.objects.filter(user_id=user, method='test').aggregate(Avg('duration'))

    stats = {
        'total_words': total_learned_words,
        'total_quizzes': total_repetitions,
        'avg_testing': str(round(avg_time_of_tests['duration__avg'], 2)),
    }

    ### Список изучаемых категорий
    categories = [l_cat.category for l_cat in Learning_Category.objects.filter(user=user)]

    ### Данные для piePlot
    learned = len(Learned_Word.objects.filter(user=user))
    in_progress = len(Word_Repetition.objects.filter(user=user))
    new_words = len(Word.objects.filter(category__in=categories)) - learned - in_progress
    set_data = [
        learned,
        in_progress,
        new_words
    ]

    pie_data = [{
        "labels": ["Learned", "In progress", "Not yet"],
        "values": set_data,
        "type": 'pie'
    }]

    ### Данные для heat plot
    # По оси x дата, по оси у время, пересечение count(session_id)
    session_new_words = (Learning_Session.objects
                         .filter(user_id=user, method='new_words')
                         .annotate(date=TruncDate('start_time'), time=ExtractHour('start_time'))
                         .values('date', 'time')
                         .annotate(count=Count('id'))
                         .order_by('date')
                         )

    date_data = [str(dt['date']) for dt in session_new_words]
    time_data = [dt['time'] for dt in session_new_words]
    count_data = [dt['count'] for dt in session_new_words]
    heat_data = [{
        'x': date_data,
        'y': time_data,
        'z': count_data,
        'type': 'heatmap',
    }]

    # илюзорная статистика
    week_dates = [(timezone.now() - timedelta(days=i)).strftime('%d.%m') for i in range(7)]
    week_progress = [
        {'date': date, 'words': random.randint(1, 10), 'quizzes': random.randint(0, 3)}
        for date in week_dates
    ]

    context = {
        'stats': stats,
        'categories': categories,
        'week_progress': week_progress,
        'pie_data': json.dumps(pie_data),
        'heat_data': json.dumps(heat_data),
    }

    return render(request, 'web/stats.html', context)


@auth_required
def reset_category_progress_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if category.owner not in [None, request.user]:
        raise PermissionDenied("Нет доступа к этой категории")

    words_in_category = Word.objects.filter(category=category)

    Learned_Word.objects.filter(
        user=request.user,
        word__in=words_in_category
    ).delete()

    Word_Repetition.objects.filter(
        user=request.user,
        word__in=words_in_category
    ).delete()

    messages.success(request, f'Прогресс по категории "{category.name}" сброшен')
    return redirect('categories_wordlist', category_id=category.id)


@auth_required
def add_word_to_category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id, owner=request.user)

    if request.method == 'POST':
        form = AddWordForm(request.POST)
        if form.is_valid():
            word_text = form.cleaned_data['word'].strip().lower()
            translation = form.cleaned_data['translation'].strip().lower()
            transcription = form.cleaned_data['transcription'].strip().lower()

            try:
                with transaction.atomic():
                    if Word.objects.filter(
                        word__iexact=word_text,
                        translation__iexact=translation,
                        transcription__iexact=transcription,
                        category=category
                    ).exists():
                        form.add_error('word', 'Это слово уже есть в данной категории')
                        return render(request, 'web/add_word.html', {'form': form, 'category': category})

                    existing_word = Word.objects.filter(
                        word__iexact=word_text,
                        translation__iexact=translation,
                        transcription__iexact=transcription
                    ).exclude(category=category).first()

                    if existing_word:
                        existing_word.category.add(category)
                        messages.success(request, 'Слово добавлено в категорию')
                    else:
                        new_word = Word.objects.create(
                            word=word_text,
                            translation=translation,
                            transcription=transcription
                        )
                        new_word.category.add(category)
                        messages.success(request, 'Слово успешно создано и добавлено')

                    return redirect('categories_wordlist', category_id=category.id)

            except IntegrityError:
                form.add_error('word', 'Ошибка: такое слово уже существует')
            except Exception as e:
                form.add_error(None, f'Ошибка: {str(e)}')

    else:
        form = AddWordForm()

    return render(request, 'web/add_word.html', {
        'form': form,
        'category': category
    })


@require_http_methods(["POST"])
@auth_required
def word_start_learning(request, word_id):
    try:
        word = Word.objects.get(id=word_id)
        if not check_word_permission(word, request.user):
            return JsonResponse({
                'status': 'error',
                'message': 'Нет доступа к этому слову'
            }, status=403)
        
        Word_Repetition.objects.get_or_create(
            user=request.user,
            word=word
        )
        return JsonResponse({'status': 'success', 'message': 'Слово добавлено в изучаемые'}, status=200)
    except Word.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Слово не найдено'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_http_methods(["POST"])
@auth_required
def word_mark_known(request, word_id):
    try:
        word = Word.objects.get(id=word_id)
        if not check_word_permission(word, request.user):
            return JsonResponse({
                'status': 'error',
                'message': 'Нет доступа к этому слову'
            }, status=403)
        
        Word_Repetition.objects.filter(user=request.user, word=word).delete()
        Learned_Word.objects.get_or_create(user=request.user, word=word)
        return JsonResponse({'status': 'success', 'message': 'Слово помечено как известное'}, status=200)
    except Word.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Слово не найдено'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_http_methods(["POST"])
@auth_required
def word_reset_progress(request, word_id):
    try:
        word = Word.objects.get(id=word_id)
        if not check_word_permission(word, request.user):
            return JsonResponse({
                'status': 'error',
                'message': 'Нет доступа к этому слову'
            }, status=403)
        
        Word_Repetition.objects.filter(user=request.user, word=word).delete()
        Learned_Word.objects.filter(user=request.user, word=word).delete()
        return JsonResponse({'status': 'success', 'message': 'Прогресс по слову сброшен'})
    except Word.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Слово не найдено'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    

@auth_required
def word_edit(request, category_id, word_id):
    category = get_object_or_404(Category, id=category_id, owner=request.user)
    word = get_object_or_404(Word, id=word_id)
    
    if not word.category.filter(owner=request.user).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        form = EditWordForm(request.POST)
        if form.is_valid():
            word_text = form.cleaned_data['word'].strip().lower()
            translation = form.cleaned_data['translation'].strip().lower()
            transcription = form.cleaned_data['transcription'].strip().lower()
            
            try:
                with transaction.atomic():
                    if Word.objects.filter(
                        word__iexact=word_text,
                        translation__iexact=translation,
                        transcription__iexact=transcription,
                        category=category
                    ).exclude(id=word.id).exists():
                        form.add_error('word', 'Такое слово уже существует в этой категории')
                        return render(request, 'web/edit_word.html', {'form': form, 'word': word})
                    
                    exact_duplicate = Word.objects.filter(
                        word__iexact=word_text,
                        translation__iexact=translation,
                        transcription__iexact=transcription
                    ).exclude(id=word.id).first()
                    
                    if exact_duplicate:
                        exact_duplicate.category.add(category)
                        
                        user = request.user
                        Word_Repetition.objects.filter(user=user, word=word).update(word=exact_duplicate)
                        Learned_Word.objects.filter(user=user, word=word).update(word=exact_duplicate)
                        Answer_Attempt.objects.filter(user=user, word=word).update(word=exact_duplicate)
                        
                        word.category.remove(category)
                        
                        messages.success(request, 'Слово объединено с существующим дубликатом')
                        return redirect('categories_wordlist', category_id=category.id)
                    
                    if word.category.count() > 1:
                        new_word = Word.objects.create(
                            word=word_text,
                            translation=translation,
                            transcription=transcription
                        )
                        new_word.category.add(category)
                        user = request.user
                        word.category.remove(category)
                        
                        messages.success(request, 'Создана новая версия слова для этой категории')
                        return redirect('categories_wordlist', category_id=category.id)
                    
                    word.word = word_text
                    word.translation = translation
                    word.transcription = transcription
                    word.save()
                    
                    messages.success(request, 'Слово успешно обновлено')
                    return redirect('categories_wordlist', category_id=category.id)
            
            except IntegrityError:
                form.add_error(None, 'Ошибка базы данных при обновлении слова')
            except Exception as e:
                form.add_error(None, f'Неожиданная ошибка: {str(e)}')
    else:
        form = EditWordForm(initial={
            'word': word.word,
            'translation': word.translation,
            'transcription': word.transcription
        })
    
    return render(request, 'web/edit_word.html', {
        'form': form,
        'word': word
    })


@auth_required
def word_delete(request, category_id, word_id):
    try:
        category = get_object_or_404(Category, id=category_id, owner=request.user)
        word = get_object_or_404(Word, id=word_id)
        
        if not word.category.filter(id=category.id).exists():
            return JsonResponse({
                'status': 'error', 
                'message': 'Слово не найдено в указанной категории'
            }, status=404)
        
        with transaction.atomic():
            categories_count = word.category.count()
            word.category.remove(category)
            
            message = 'Слово удалено из категории' if categories_count > 1 else 'Слово полностью удалено'
            
            return JsonResponse({
                'status': 'success', 
                'message': message
            })
            
    except Http404:
        return JsonResponse({
            'status': 'error', 
            'message': 'Категория или слово не найдены'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': f'Ошибка при удалении: {str(e)}'
        }, status=400)


@require_http_methods(["POST"])
@auth_required(redirect_to_login=False)
def update_user_categories(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = request.user
        category = Category.objects.get(id=data['category_id'])

        if category.owner not in [None, user]:
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
    

@require_http_methods(["POST"])
@auth_required(redirect_to_login=False)
def new_word_send_result(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = request.user
        word_id = data.get('word_id')
        is_known = data.get('is_known')

        if None in (word_id, is_known):
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required fields'
            }, status=400)

        try:
            word = Word.objects.get(id=word_id)
        except Word.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Word not found'
            }, status=404)
        
        if not check_word_permission(word, user):
            return JsonResponse({
                'status': 'error', 
                'message': 'No permission for this word'
            }, status=403)

        if is_known:
            Learned_Word.objects.get_or_create(user=user, word_id=word_id)
            return JsonResponse({
                'status': 'success', 
                'message': 'Known word added'
            }, status=200)
    
        Word_Repetition.objects.update_or_create(
            user=user,
            word_id=word_id,
            defaults={'next_review': timezone.now() + timedelta(seconds=30)}
        )
        return JsonResponse({'status': 'success', 'message': 'Word to learned added'}, status=200)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    

@require_http_methods(["GET"])
@auth_required(redirect_to_login=False)
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


@require_http_methods(["GET"])
@auth_required(redirect_to_login=False)
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
        words_to_repeat = Word.objects.filter(id__in=words_ids)
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


@require_http_methods(["POST"])
@auth_required(redirect_to_login=False)
def send_repeat_result(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = request.user
        word_id = data.get('word_id')
        session_id = data.get('session_id')
        is_known = data.get('is_known')
        now = timezone.now()

        if None in (word_id, session_id, is_known):
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required fields'
            }, status=400)
        
        try:
            session = Learning_Session.objects.get(id=session_id)
            if session.user != user:
                return JsonResponse({
                    'status': 'error',
                    'message': 'This session does not belong to the current user'
                }, status=403)
        except Learning_Session.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Learning session not found'
            }, status=404)

        try:
            word = Word.objects.get(id=word_id)
            if not check_word_permission(word, user):
                return JsonResponse({
                    'status': 'error',
                    'message': 'No permission for this word'
                }, status=403)
        except Word.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Word not found'
            }, status=404)

        try:
            repetition = Word_Repetition.objects.get(user=user, word_id=word_id)
            if repetition.next_review >= now:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Word is not ready for repetition yet. Next review at {repetition.next_review}'
                }, status=400)
        except Word_Repetition.DoesNotExist:
            repetition = Word_Repetition.objects.create(
                user=user,
                word_id=word_id,
                next_review=now + timedelta(minutes=REPETITION_INTERVALS[0])
            )

        Answer_Attempt.objects.create(
            user=user,
            word_id=word_id,
            session_id=session_id,
            is_correct=is_known
        )

        if is_known:
            if repetition.repetition_count == 5:
                repetition.delete()
                Learned_Word.objects.create(user=user, word_id=word_id)
                message = 'Word learned!'
            else:
                repetition.repetition_count += 1
                repetition.next_review = now + timedelta(
                    minutes=REPETITION_INTERVALS.get(repetition.repetition_count, 0)
                )
                repetition.save()
                message = 'Repetition updated'
        else:
            repetition.repetition_count = max(0, repetition.repetition_count - 1)
            repetition.next_review = now + timedelta(
                minutes=REPETITION_INTERVALS.get(repetition.repetition_count, 0)
            )
            repetition.save()
            message = 'Word difficulty increased'
                 
        return JsonResponse({'status': 'success', 'message': message}, status=200)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_http_methods(["GET"])
@auth_required(redirect_to_login=False)
def get_test_questions(request):
    try:
        user = request.user
        category_id = request.GET.get('category_id')

        if not category_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Category ID is required'
            }, status=400)
        
        try:
            category = Category.objects.get(id=category_id)
            if category.owner and category.owner != user:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No permission for this category'
                }, status=403)
        except Category.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Category not found'
            }, status=404)

        words = list(Word.objects.filter(category__id=category_id).values('id', 'word', 'transcription', 'translation'))
        
        if not words:
            return JsonResponse({'status': 'success', 'questions': []})
        
        questions = generate_test_questions(words)
        return JsonResponse({'status': 'success', 'questions': questions})

    except Exception as e:
        return JsonResponse({'status': 'error','error': str(e)}, status=500)


@require_http_methods(["GET"])
def search_words(request):
    try:
        query = request.GET.get('q', '').strip().lower()
        user = request.user

        if len(query) < 2:
            return JsonResponse({'status': 'success', 'count': 0, 'results': []})

        words = Word.objects.filter(
            Q(word__icontains=query) | Q(translation__icontains=query)
        ).distinct()

        exact_matches = []
        partial_matches = []

        for word in words:
            accessible_categories = word.category.filter(
                Q(owner__isnull=True) |  # Общие категории
                Q(owner=request.user.id if user.is_authenticated else None)  # Категории пользователя
            )

            for category in accessible_categories:
                item = {
                    'word': word.word,
                    'translation': word.translation,
                    'transcription': word.transcription,
                    'category_name': category.name,
                    'category_id': category.id,
                    'is_private': category.owner is not None
                }

                if word.word.lower() == query or word.translation.lower() == query:
                    exact_matches.append(item)
                else:
                    partial_matches.append(item)

        results = exact_matches + partial_matches

        return JsonResponse({
            'status': 'success',
            'count': len(results),
            'results': results
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    

@require_http_methods(["POST"])
@auth_required(redirect_to_login=False)
def track_session(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = request.user

        if 'type' not in data:
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required field: type'
            }, status=400)
        
        if data['type'] == 'session_start':
            return handle_session_start(user, data)
        
        if data['type'] == 'session_end':
            return handle_session_end(user, data)

        return JsonResponse({
            'status': 'error',
            'message': 'Invalid session type'
        }, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)