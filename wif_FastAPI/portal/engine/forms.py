from starlette_wtf import StarletteForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import (
    DataRequired, Length, Email, EqualTo, ValidationError)
from fastapi import Request

try:
    from StealthPortal.wif_FastAPI.portal.engine import models, get_db
    from StealthPortal.wif_FastAPI.portal.security.auth import verify_passwd
except ImportError:
    from portal.engine import models, get_db
    from portal.security.auth import verify_passwd


class RegistrationForm(StarletteForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(),
                                                 EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        db = next(get_db())
        user = db.query(models.User).filter(
            models.User.username == username.data).first()

        if user:
            raise ValidationError(
                'That username is taken. Please choose a different one.')

    def validate_email(self, email):
        db = next(get_db())
        user = db.query(models.User).filter(
            models.User.email == email.data).first()

        if user:
            raise ValidationError(
                'That email is taken. Please choose a different one.')


class LoginForm(StarletteForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

    def validate_email(self, email):
        db = next(get_db())
        user = db.query(models.User).filter(
            models.User.email == email.data).first()
        if not user:
            raise ValidationError(
                'Incorrect user email. '
                'Please verify you entered the correct email.')
        self.user = user

    def validate_password(self, password):
        if hasattr(self, 'user') and not verify_passwd(
                password.data.encode('utf-8'), self.user.password):
            raise ValidationError('Incorrect password. Please try again.')


class UpdateProfileForm(StarletteForm):
    def __init__(self, request, current_user=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.current_user = current_user

    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != self.current_user.username:
            db = next(get_db())
            user = db.query(models.User).filter(
                models.User.username == username.data).first()
            if user:
                raise ValidationError(
                    'That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != self.current_user.email:
            db = next(get_db())
            user = db.query(models.User).filter(
                models.User.email == email.data).first()
            if user:
                raise ValidationError(
                    'That email is taken. Please choose a different one.')
