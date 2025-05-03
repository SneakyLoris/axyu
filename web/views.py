from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q, Case, When, Value, Exists, OuterRef, CharField
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.conf import settings


import os

from api.models import User, Category, Word, Learning_Category, \
    Learned_Word, Word_Repetition
from foreign_words.settings import BASE_DIR
from web.forms import RegistrationForm, AuthForm, FeedbackForm, AddCategoryForm, EditCategoryForm


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
        # Либо выбрасывать 404, мол такой страницы нет - raise Http404("Категория не найдена или недоступна")
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