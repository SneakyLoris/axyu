from django.contrib.auth import authenticate, login, logout
from django.db.models import Q, Case, When, Value, Exists, OuterRef, CharField
from django.shortcuts import render, redirect

from api.models import User, Category, Word, Learning_Category, \
    Learned_Word, Word_Repetition
from web.forms import RegistrationForm, AuthForm


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

            print(form.cleaned_data)

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
                return redirect("main")

    return render(request, "web/auth.html", {
        "form": form,
    })


def logout_view(request):
    logout(request)
    return redirect("main")


def stats_view(request):
    return render(request, "web/stats.html")


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
        wordlist = Word.objects.filter(category=category).annotate(
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
                output_field=CharField())
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
    # БУДЕТ ФОРМА
    return render(request, "web/stats.html")


def remove_category_view(request):
    # БУДЕТ УДАЛЕНИЕ КАТЕГОРИИ
    return redirect("web/main.html")
