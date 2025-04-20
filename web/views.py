from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from web.models import User, Category, Word

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
    return render(request, "web/learning.html")

def learning_tests_view(request):
    return render(request, "web/learning.html")


def categories_view(request):
    categories = Category.objects.all()

    return render(request, "web/categories.html", {
        "categories": categories,
    })


def categories_wordlist_view(request, category_name):
    try:
        category = Category.objects.get(name=category_name)
        wordlist = Word.objects.filter(category=category)
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
