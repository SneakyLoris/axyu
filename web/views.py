import os
from datetime import datetime, timedelta
import random
import json

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models.functions import Coalesce
from django.db.models import Q, Case, When, Value, Exists, OuterRef, CharField, Subquery
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.db.models import Q, Case, When, Value, Exists, OuterRef, CharField
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.conf import settings


import os

from psycopg2 import IntegrityError

from api.models import User, Category, Word, Learning_Category, \
    Learned_Word, Word_Repetition, Answer_Attempt
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
            if user is None:
                form.add_error(None, "Введены неверные данные")
            else:
                login(request, user)
                # Session.objects.create(user=user)
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


def learning_view(request):
    return render(request, "web/learning.html")


def learning_new_words_view(request):
    return render(request, "web/new_words.html")


def learning_repeat_view(request):
    return render(request, "web/repeat_words.html")


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


def category_test(request):
    category_id = request.GET.get('category_id', '')

    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        # Либо выбрасывать 404, мол такой страницы нет
        category = None

    return render(request, "web/tests.html", {
        "category": category,
    })


def categories_wordlist_view(request, category_name):
    try:
        category = Category.objects.get(name=category_name)
        user = request.user if request.user.is_authenticated else None

        # Базовый запрос для слов категории
        words = Word.objects.filter(category=category)

        # Если пользователь аутентифицирован - добавляем аннотации
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

            # Добавляем прогресс в контекст (5 повторений = 100%)
            wordlist = list(wordlist)
            for word in wordlist:
                word.repetition_progress = min(100, word.repetition_count * 20)
        else:
            # Для неаутентифицированных пользователей
            wordlist = words.annotate(
                status=Value('new', output_field=CharField()),
                repetition_count=Value(0),
                repetition_progress=Value(0)
            ).distinct()

    except Category.DoesNotExist:
        # Либо выбрасывать 404, мол такой страницы нет
        category = None
        wordlist = None

    return render(request, "web/category_contains.html", {
        "wordlist": wordlist,
        "category": category,
        "highlight_word": request.GET.get('highlight', ''),
    })


@login_required
def remove_category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id, owner=request.user)

    user_upload_dir = os.path.join(settings.BASE_DIR, 'wordlists', 'translated', 'user_uploads', str(request.user.id))
    file_path = os.path.join(user_upload_dir, f"{category.name}.txt")

    if os.path.exists(file_path):
        os.remove(file_path)

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
        form = AddCategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save(commit=False)
            category.owner = request.user
            category.save()

            word_file = request.FILES['word_file']
            user_upload_dir = os.path.join(BASE_DIR, 'wordlists', 'translated', 'user_uploads', str(request.user.id))
            os.makedirs(user_upload_dir, exist_ok=True)

            file_name = f"{category.name}.txt"
            file_path = os.path.join(user_upload_dir, file_name)

            with default_storage.open(file_path, 'wb+') as destination:
                for chunk in word_file.chunks():
                    destination.write(chunk)

            try:
                call_command(
                    'load_words',
                    os.path.abspath(user_upload_dir),
                    verbosity=0
                )
            except Exception as e:
                print(f"Error loading words: {e}")
                return render(request, 'web/add_category.html', {
                    'form': form,
                    'error': 'Ошибка при загрузке слов. Проверьте формат файла.'
                })

            return redirect('categories')
    else:
        form = AddCategoryForm()

    return render(request, 'web/add_category.html', {'form': form})


@login_required
def edit_category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id, owner=request.user)
    old_name = category.name
    file_changed = False

    if request.method == 'POST':
        form = EditCategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            new_category = form.save()
            user_upload_dir = os.path.join(BASE_DIR, 'wordlists', 'translated', 'user_uploads', str(request.user.id))
            old_file_path = os.path.join(user_upload_dir, f"{old_name}.txt")
            new_file_path = os.path.join(user_upload_dir, f"{new_category.name}.txt")

            # Обработка нового файла
            if 'word_file' in request.FILES:
                file_changed = True
                new_file = request.FILES['word_file']

                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

                # Сохраняем новый файл
                with default_storage.open(new_file_path, 'wb+') as destination:
                    for chunk in new_file.chunks():
                        destination.write(chunk)

            # Переименование файла, если изменилось название категории (без замены файла)
            elif old_name != new_category.name and os.path.exists(old_file_path):
                os.rename(old_file_path, new_file_path)

            if file_changed:
                try:
                    Word.objects.filter(category=category).delete()
                    call_command(
                        'load_words',
                        os.path.abspath(user_upload_dir),
                        verbosity=0
                    )
                except Exception as e:
                    print(f"Error loading words: {e}")
                    messages.error(request, 'Ошибка при загрузке слов. Проверьте формат файла.')
                    return redirect('edit_category', category_id=category.id)

            return redirect('categories_wordlist', category_name=new_category.name)
    else:
        form = EditCategoryForm(instance=category)

    return render(request, 'web/edit_category.html', {
        'form': form,
        'category': category
    })


def stats_view(request):
    user = request.user

    # Эвелинино
    total_learned_words = len(Learned_Word.objects.filter(user=user))
    total_repetitions = len(Answer_Attempt.objects.filter(user=user))

    stats = {
        'total_words': total_learned_words,
        'total_quizzes': total_repetitions,
        'success_rate': random.randint(60, 95),
    }

    # результат за неделю
    week_dates = [(datetime.now() - timedelta(days=i)).strftime('%d.%m') for i in range(7)]
    week_progress = [
        {'date': date, 'words': random.randint(1, 10), 'quizzes': random.randint(0, 3)}
        for date in week_dates
    ]

    # Конец Эвелининого соло

    ### Список изучаемых категорий
    categories = [l_cat.category for l_cat in Learning_Category.objects.filter(user=user)]

    """
    Хочу добавить к каждой категории сколько слов выучено
    for cat in cats:
        categories[cat.category.name] = 
    """

    ### Данные для piePlot
    learned = len(Learned_Word.objects.filter(user=user))
    in_progress = len(Word_Repetition.objects.filter(user=user))
    new_words = len(Word.objects.filter(category__in=categories)) - learned - in_progress
    set_data = [
        learned,
        in_progress,
        new_words
    ]

    pie_data = {
        "labels": ["Learned", "In progress", "Not yet"],
        "datasets": [{
            "label": "some phrase",
            "data": set_data,
            "backgroundColor": [
                'green',
                'yellow',
                'red'
            ],
        }]
    }

    ### Данные для графика посещения

    #### Количество посещений в день
    """sessions_count = (Session.objects
                      .filter(user=user)
                      .annotate(date=TruncDate('start_time'))
                      .values('date')
                      .annotate(count=Count('id'))
                      .order_by('date')
                      )

    labels = [line["date"] for line in sessions_count]
    data = [line["count"] for line in sessions_count]

    visit_count_dataset = {
        "labels": labels,
        "datasets": [{
            "label": "Количество входов на сайт",
            "data": data,
        }]
    }

    #### Время проведенное в день
    def covert_time_to_hour(time: timedelta):
        return time.seconds / 3600

    sessions_time = (Session.objects
                     .filter(user=user)
                     .annotate(date=TruncDate('start_time'))
                     .values('date')
                     .annotate(sum=Sum(F('end_time') - F('start_time')))
                     .order_by('date')
                     )

    data = [covert_time_to_hour(line["sum"]) for line in sessions_time]
    labels = [line["date"] for line in sessions_time]

    visit_time_dataset = {
        "labels": labels,
        "datasets": [{
            "label": "Время проведенное на сайте",
            "data": data,
        }]
    }
"""
    """
    Список того, что можно визуализировать
    - Изучаемые категории [х]
    - Круговая диаграмма выученных слов (всего слов и сколько из них на стадии изучения и выученных) [x]
    - График посещений страницы/время проведения на сайте (lineplot типа времени в день) []
    - График выученных слов по дням/неделям/месяцам (гистограмма) []
    """

    context = {
        'stats': stats,
        'categories': categories,
        'week_progress': week_progress,
        'pie_data': json.dumps(pie_data),
        #'session_count_data': json.dumps(visit_count_dataset, cls=DjangoJSONEncoder),
        #'session_time_data': json.dumps(visit_time_dataset, cls=DjangoJSONEncoder),
    }

    return render(request, 'web/stats.html', context)


@login_required
def reset_category_progress_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)

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
    return redirect('categories_wordlist', category_name=category.name)


@login_required
def add_word_to_category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id, owner=request.user)

    if request.method == 'POST':
        form = AddWordForm(request.POST)
        if form.is_valid():
            word_text = form.cleaned_data['word'].strip().lower()
            translation = form.cleaned_data['translation'].strip().lower()
            transcription = form.cleaned_data['transcription'].strip()

            if Word.objects.filter(word__iexact=word_text, category=category).exists():
                form.add_error('word', 'Это слово уже есть в данной категории')
            else:
                try:
                    existing_word = Word.objects.filter(word__iexact=word_text).first()

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

                    return redirect('categories_wordlist', category_name=category.name)

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

@login_required
def word_start_learning(request, word_id):
    try:
        word = Word.objects.get(id=word_id)
        Word_Repetition.objects.update_or_create(
            user=request.user,
            word=word
        )
        return JsonResponse({'status': 'success', 'message': 'Слово добавлено в изучаемые'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def word_mark_known(request, word_id):
    try:
        word = Word.objects.get(id=word_id)
        Word_Repetition.objects.filter(user=request.user, word=word).delete()
        Learned_Word.objects.get_or_create(user=request.user, word=word)
        return JsonResponse({'status': 'success', 'message': 'Слово помечено как известное'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def word_reset_progress(request, word_id):
    try:
        word = Word.objects.get(id=word_id)
        Word_Repetition.objects.filter(user=request.user, word=word).delete()
        Learned_Word.objects.filter(user=request.user, word=word).delete()
        return JsonResponse({'status': 'success', 'message': 'Слово помечено как известное'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
@login_required
def word_edit(request, word_id):
    word = get_object_or_404(Word, id=word_id)
    
    if not word.category.filter(owner=request.user).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        form = EditWordForm(request.POST)
        if form.is_valid():
            word_text = form.cleaned_data['word'].strip().lower()
            translation = form.cleaned_data['translation'].strip().lower()
            transcription = form.cleaned_data['transcription'].strip()
            
            if Word.objects.filter(word__iexact=word_text).exclude(id=word.id).exists():
                form.add_error('word', 'Такое слово уже существует')
            else:
                try:
                    word.word = word_text
                    word.translation = translation
                    word.transcription = transcription
                    word.save()
                    messages.success(request, 'Слово успешно обновлено')
                    
                    first_category = word.category.first()
                    return redirect('categories_wordlist', category_name=first_category.name)
                
                except Exception as e:
                    form.add_error(None, f'Ошибка: {str(e)}')
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
def word_delete(request, word_id):
    try:
        Word.objects.get(id=word_id).delete()
        return JsonResponse({'status': 'success', 'message': 'Слово удалено'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)