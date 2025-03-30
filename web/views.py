from django.shortcuts import render


def main_view(request):
    return render(request, "web/main.html")


def registration_view(request):
    pass


def auth_view(request):
    pass


def goods_view(request, value):
    pass


def good_view(request, value):
    pass
