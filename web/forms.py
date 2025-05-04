from django import forms
from django.contrib.auth import get_user_model

from api.models import Feedback, Category, Word

User = get_user_model()


class RegistrationForm(forms.ModelForm):
    password2 = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data["password"] != cleaned_data["password2"]:
            self.add_error("password", "Пароли не совпадают")

        return cleaned_data

    class Meta:
        model = User
        fields = ("email", "username", "password", "password2")


class AuthForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'id': 'id_name',
                'class': 'form-control',
            }),
            'email': forms.EmailInput(attrs={
                'id': 'id_email',
                'class': 'form-control',
            }),
            'message': forms.Textarea(attrs={
                'id': 'id_message',
                'class': 'form-control',
                'rows': 5,
            }),
        }


class AddCategoryForm(forms.ModelForm):
    word_file = forms.FileField(
        label='Файл со словами',
        help_text='Загрузите .txt файл со словами в формате: слово;перевод;транскрипция'
    )

    class Meta:
        model = Category
        fields = ['name', 'description']
        labels = {
            'name': 'Название категории',
            'description': 'Описание (необязательно)'
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        error_messages = {
            'name': {
                'unique': "Категория с таким названием уже существует.",
            }
        }

class EditCategoryForm(forms.ModelForm):
    word_file = forms.FileField(
        label='Новый файл со словами',
        help_text='Загрузите новый .txt файл (старый будет удален)',
        required=False
    )

    class Meta:
        model = Category
        fields = ['name', 'description']
        labels = {
            'name': 'Название категории',
            'description': 'Описание'
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        error_messages = {
            'name': {
                'unique': "Категория с таким названием уже существует.",
            }
        }

class AddWordForm(forms.Form):
    word = forms.CharField(
        label='Английское слово',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    translation = forms.CharField(
        label='Перевод',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    transcription = forms.CharField(
        label='Транскрипция',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )