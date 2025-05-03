import os
from datetime import datetime, timedelta
import random
import json

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models.functions import Coalesce
from django.db.models import Q, Case, When, Value, Exists, OuterRef, CharField, Subquery
from django.shortcuts import render, redirect

from api.models import User, Category, Word, Learning_Category, \
    Learned_Word, Word_Repetition, Answer_Attempt
from web.forms import RegistrationForm, AuthForm, FeedbackForm


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
    })


def add_category_view(request):
    # Времеенное решение для заполнения страницы категориями
    os.system("python manage.py load_words wordlists/translated")
    return redirect("categories")


def remove_category_view(request, category_name):
    Category.objects.get(name=category_name).delete()
    return redirect("categories")


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
