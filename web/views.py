from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from web.models import User

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


def goods_view(request, value):
    # Тут модельки надо определить, чтобы что-то делать дальше
    pass


def good_view(request, value):
    pass
