from django import forms
from django.contrib.auth import get_user_model

from api.models import Feedback

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