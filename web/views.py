import os
from datetime import timedelta
import random
import json

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.functions import  Coalesce, TruncDate, TruncTime, ExtractHour
from django.db.models import Avg, Q, Case, Count, When, Value, Exists, OuterRef, CharField, Subquery
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect
from django.db.models import Q, Case, When, Value, Exists, OuterRef, CharField
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.conf import settings
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.http import require_http_methods

import os

from psycopg2 import IntegrityError

from api.models import User, Category, Word, Learning_Category, \
    Learned_Word, Word_Repetition, Answer_Attempt, Learning_Session
from foreign_words.settings import BASE_DIR
from web.forms import RegistrationForm, AuthForm, FeedbackForm, AddCategoryForm, EditCategoryForm, AddWordForm, EditWordForm


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

    return render(request, "web/auth.html", {
        "form": form,
    })


def logout_view(request):
    user = request.user

    """try:
        session = Session.objects.order_by("-start_time").filter(user=user).first()
        session.end_time = datetime.now()
        session.save()
    except Session.DoesNotExist:
        Session.objects.create(user=user, end_time=datetime.now())"""

    logout(request)
    return redirect("main")

@login_required
def learning_view(request):
    return render(request, "web/learning.html")

@login_required
def learning_new_words_view(request):
    return render(request, "web/new_words.html")

@login_required
def learning_repeat_view(request):
    return render(request, "web/repeat_words.html")


@login_required
def learning_tests_view(request):
    categories = Category.objects.filter(
        Q(owner__isnull=True) | Q(owner_id=request.user.id)
    )
    user_selected = Learning_Category.objects.filter(
        user_id=request.user.id
    )
    user_selected_categories = user_selected.values_list('category_id', flat=True)

    return render(request, "web/select_test.html", {
        "categories": categories,
        "user_selected_categories": user_selected_categories
    })


def categories_view(request):
    categories = Category.objects.filter(
        Q(owner__isnull=True) | Q(owner_id=request.user.id)
    )
    user_selected = Learning_Category.objects.filter(
        user_id=request.user.id
    )
    user_selected_categories = user_selected.values_list('category_id', flat=True)

    return render(request, "web/categories.html", {
        "categories": categories,
        "user_selected_categories": user_selected_categories
    })


@login_required
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

    return render(request, "web/tests.html", {
        "category": category,
    })


def categories_wordlist_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    user = request.user if request.user.is_authenticated else None

    if category.owner not in [None, user]:
            raise PermissionDenied("Нет доступа к этой категории")

    words = Word.objects.filter(category=category)

    if user:
        wordlist = words.annotate(
            status=Case(
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
            repetition_count=Coalesce(
                Subquery(
                    Word_Repetition.objects.filter(
                        word=OuterRef('pk'),
                        user=user
                    ).values('repetition_count')[:1]
                ),
                Value(0)
            )
        ).distinct()

        wordlist = list(wordlist)
        for word in wordlist:
            word.repetition_progress = min(100, word.repetition_count * 20)
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

@login_required
def remove_category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id, owner=request.user)

    upload_path = os.path.join(
        'tmp',
        str(request.user.id),
        f'{category.name}.txt'
    )
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


@login_required
def add_category_view(request):
    if request.method == 'POST':
        form = AddCategoryForm(request.POST, request.FILES, user=request.user)
        if not form.is_valid():
            return render(request, 'web/add_category.html', {'form': form}, status=400)

        category = form.save(commit=False)
        category.owner = request.user
        category.save()

        word_file = request.FILES.get('word_file')

        upload_path = os.path.join(
            'tmp', 
            str(request.user.id),
            f'{category.name}.txt'
        )   

        file_path = default_storage.save(upload_path, word_file)
        absolute_file_path = default_storage.path(file_path)
            
        with default_storage.open(file_path, 'wb+') as destination:
            for chunk in word_file.chunks():
                destination.write(chunk)

        try:
            call_command(
                'load_words',
                dir_path=os.path.dirname(absolute_file_path),
                user_name=request.user.username,
                verbosity=0
            )

        except Exception :
            default_storage.delete(upload_path)
            return render(request, 'web/add_category.html', {
                'form': form,
                'error': 'Ошибка при загрузке слов. Проверьте формат файла.'
            }, status=400)

        return redirect('categories')
    else:
        form = AddCategoryForm()

    return render(request, 'web/add_category.html', {'form': form})


@login_required
def edit_category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id, owner=request.user)

    if request.method == 'POST':
        form = EditCategoryForm(
            request.POST, 
            request.FILES, 
            instance=category, 
            user=request.user
        )
        
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


@login_required
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


@login_required
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

            except IntegrityError as e:
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
@login_required
def word_start_learning(request, word_id):
    try:
        word = Word.objects.get(id=word_id)

        if not word.category.filter(Q(owner=request.user) | Q(owner__isnull=True)).exists():
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
@login_required
def word_mark_known(request, word_id):
    try:
        word = Word.objects.get(id=word_id)

        if not word.category.filter(Q(owner=request.user) | Q(owner__isnull=True)).exists():
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
@login_required
def word_reset_progress(request, word_id):
    try:
        word = Word.objects.get(id=word_id)

        if not word.category.filter(Q(owner=request.user) | Q(owner__isnull=True)).exists():
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
    
@login_required
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
            
            except IntegrityError as e:
                form.add_error(None, 'Ошибка базы данных при обновлении слова')
            except Exception as e:
                print(e)
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


@login_required
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
            
            if categories_count > 1:
                message = 'Слово удалено из категории'
            else:
                message = 'Слово полностью удалено'
            
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
    
