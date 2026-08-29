from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateTimeField, SubmitField, FileField, BooleanField
from wtforms.validators import DataRequired, Length, Email, ValidationError, Optional
from flask_wtf.file import FileAllowed, FileRequired
from datetime import datetime, timedelta

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    name = StringField('Имя', validators=[DataRequired()])
    phone = StringField('Телефон', validators=[DataRequired()])
    user_type = SelectField('Тип пользователя', choices=[('client', 'Клиент'), ('lawyer', 'Юрист')])
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class OrderForm(FlaskForm):
    service_type = SelectField('Тип услуги', choices=[
        ('consultation', 'Консультация'),
        ('document', 'Составление документа'),
        ('court', 'Представление интересов в суде'),
        ('government', 'Представление интересов в госорганах')
    ], validators=[DataRequired()])
    description = TextAreaField('Опишите вашу проблему', validators=[DataRequired()])
    location = StringField('Место', validators=[DataRequired()])
    date = DateTimeField('Дата и время', format='%Y-%m-%d %H:%M', validators=[Optional()])
    submit = SubmitField('Заказать')

class LawyerRegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    name = StringField('ФИО полностью', validators=[DataRequired()])
    phone = StringField('Телефон', validators=[DataRequired()])
    
    passport_series = StringField('Серия паспорта', validators=[DataRequired()])
    passport_number = StringField('Номер паспорта', validators=[DataRequired()])
    passport_issued = StringField('Кем выдан', validators=[DataRequired()])
    passport_date = StringField('Дата выдачи', validators=[DataRequired()])
    birth_date = StringField('Дата рождения', validators=[DataRequired()])
    
    passport_file = FileField('Скан паспорта (главный разворот + прописка)', 
                              validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Только изображения и PDF!')])
    inn_file = FileField('Скан ИНН', 
                         validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Только изображения и PDF!')])
    snils_file = FileField('Скан СНИЛС', 
                           validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Только изображения и PDF!')])
    diploma_file = FileField('Скан диплома о высшем юридическом образовании', 
                             validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Только изображения и PDF!')])
    photo_file = FileField('Ваше фото (как на документы)', 
                           validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png'], 'Только изображения!')])
    
    is_lawyer = BooleanField('Являюсь адвокатом')
    lawyer_license_file = FileField('Скан удостоверения адвоката', 
                                    validators=[FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Только изображения и PDF!')])
    registry_extract_file = FileField('Выписка из реестра адвокатов', 
                                      validators=[FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Только изображения и PDF!')])
    
    agree_terms = BooleanField('Я согласен с условиями Пользовательского соглашения', validators=[DataRequired()])
    agree_data = BooleanField('Даю согласие на обработку персональных данных', validators=[DataRequired()])
    agree_check = BooleanField('Согласен на проверку предоставленных данных', validators=[DataRequired()])
    
    submit = SubmitField('Отправить на проверку')
