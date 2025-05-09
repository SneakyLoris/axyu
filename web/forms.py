from django import forms
from django.contrib.auth import get_user_model

from web.models import Category, Feedback

User = get_user_model()


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=True)
    password2 = forms.CharField(widget=forms.PasswordInput(), required=True)

    class Meta:
        model = User
        fields = ("email", "username", "password", "password2")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким именем уже существует")
        return username

    def clean(self):
        cleaned_data = super().clean()

        required_fields = ("email", "username", "password", "password2")
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, 'Это поле обязательно для заполнения')
        
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
    
        if password and password2 and password != password2:
            self.add_error("password2", "Пароли не совпадают")

        return cleaned_data


class AuthForm(forms.Form):
    username = forms.CharField(required=True, error_messages={
        'required': 'Обязательное поле'
    })
    password = forms.CharField(
        widget=forms.PasswordInput(),
        required=True,
        error_messages={
            'required': 'Обязательное поле'
        }
    )


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

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        
        if not self.current_user:
            raise forms.ValidationError("Пользователь не определен")
        
        if Category.objects.filter(name=name, owner=self.current_user).exists():
            raise forms.ValidationError("У вас уже есть категория с таким названием.")
        
        if Category.objects.filter(name=name, owner=None).exists():
            raise forms.ValidationError("Категория с таким названием уже существует как общая.")
        
        return name
    

class EditCategoryForm(forms.ModelForm):
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

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.original_name = self.instance.name if self.instance else None

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        
        if not name:
            raise forms.ValidationError("Обязательное поле.")

        if not self.current_user:
            raise forms.ValidationError("Пользователь не определен")
        
        if hasattr(self, 'original_name') and name == self.original_name:
            return name
            
        if Category.objects.filter(name=name, owner=self.current_user).exists():
            raise forms.ValidationError("У вас уже есть категория с таким названием.")
        
        if Category.objects.filter(name=name, owner=None).exists():
            raise forms.ValidationError("Категория с таким названием уже существует как общая.")
            
        return name


class AddWordForm(forms.Form):
    word = forms.CharField(
        label='Английское слово',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
        error_messages={
            'required': 'Поле "Английское слово" обязательно для заполнения',
            'max_length': 'Максимальная длина английского слова - 50 символов'
        }
    )
    translation = forms.CharField(
        label='Перевод',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
        error_messages={
            'required': 'Поле "Перевод" обязательно для заполнения',
            'max_length': 'Максимальная длина перевода - 50 символов'
        }
    )
    transcription = forms.CharField(
        label='Транскрипция (необязательно)',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        empty_value='',
        error_messages={
            'max_length': 'Максимальная длина транскрипции - 50 символов'
        }
    )


class EditWordForm(forms.Form):
    word = forms.CharField(
        label='Английское слово',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
        error_messages={
            'required': 'Поле "Английское слово" обязательно для заполнения',
            'max_length': 'Максимальная длина английского слова - 50 символов'
        }
    )
    translation = forms.CharField(
        label='Перевод',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
        error_messages={
            'required': 'Поле "Перевод" обязательно для заполнения',
            'max_length': 'Максимальная длина перевода - 50 символов'
        }
    )
    transcription = forms.CharField(
        label='Транскрипция',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'max_length': 'Максимальная длина транскрипции - 50 символов'
        }
    )