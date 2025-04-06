from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise ValidationError('Passwords do not match.')

        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError(
                'That username is taken. Please choose a different one.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                'That email is taken. Please choose a different one.')
        return email


class LoginForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    remember = forms.BooleanField(required=False)


class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super(UpdateProfileForm, self).__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username != self.current_user.username:
            if User.objects.filter(username=username).exists():
                raise ValidationError(
                    'That username is taken. Please choose a different one.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email != self.current_user.email:
            if User.objects.filter(email=email).exists():
                raise ValidationError(
                    'That email is taken. Please choose a different one.')
        return email
