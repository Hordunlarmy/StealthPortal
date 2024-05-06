from starlette_wtf import StarletteForm
# from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import (
    DataRequired, Length, Email, EqualTo, ValidationError)
from portal.engine import models, get_db


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


class UpdateProfileForm(StarletteForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Update')

    def validate_username(self, username):
        db = next(get_db())
        if username.data != current_user.username:
            user = db.query.filter_by(
                models.User.username == username.data).first()
            if user:
                raise ValidationError(
                    'That username is taken. Please choose a different one.')

    def validate_email(self, email):
        db = next(get_db())
        if email.data != current_user.email:
            user = db.query.filter_by(model.User.email == email.data).first()
            if user:
                raise ValidationError(
                    'That email is taken. Please choose a different one.')
