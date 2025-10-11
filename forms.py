from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Email jest wymagany'),
        Email(message='Podaj poprawny adres email')
    ])
    password = PasswordField('Hasło', validators=[
        DataRequired(message='Hasło jest wymagane'),
        Length(min=6, message='Hasło musi mieć minimum 6 znaków')
    ])
    confirm_password = PasswordField('Potwierdź hasło', validators=[
        DataRequired(message='Potwierdź hasło'),
        EqualTo('password', message='Hasła muszą być identyczne')
    ])
    submit = SubmitField('Zarejestruj się')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Email jest wymagany'),
        Email(message='Podaj poprawny adres email')
    ])
    password = PasswordField('Hasło', validators=[
        DataRequired(message='Hasło jest wymagane')
    ])
    submit = SubmitField('Zaloguj się')
