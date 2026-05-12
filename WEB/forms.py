from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from models import User, Tag

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя уже занято.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже используется.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class StrategyForm(FlaskForm):
    title = StringField('Название стратегии', validators=[DataRequired()])
    game = StringField('Название игры', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    image = FileField('Скриншот (необязательно)', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Только изображения!')
    ])
    tags = SelectMultipleField('Теги', coerce=int)
    submit = SubmitField('Опубликовать')

class CommentForm(FlaskForm):
    text = TextAreaField('Комментарий', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Отправить')

class DeleteForm(FlaskForm):
    submit = SubmitField('Удалить стратегию')

class DiceForm(FlaskForm):
    bet_amount = IntegerField('Сумма ставки (баллы)', validators=[DataRequired(), NumberRange(min=1)])
    bet_number = IntegerField('Ваше число (2–12)', validators=[DataRequired(), NumberRange(min=2, max=12)])
    submit = SubmitField('Бросить кубики')

class RouletteForm(FlaskForm):
    bet_amount = IntegerField('Сумма ставки (баллы)', validators=[DataRequired(), NumberRange(min=1)])
    bet_number = IntegerField('Ваше число (0–36)', validators=[DataRequired(), NumberRange(min=0, max=36)])
    submit = SubmitField('Запустить рулетку')

class SlotsForm(FlaskForm):
    bet_amount = IntegerField('Сумма ставки (баллы)', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Крутить барабаны')

class GuessForm(FlaskForm):
    bet_amount = IntegerField('Сумма ставки (баллы)', validators=[DataRequired(), NumberRange(min=1)])
    bet_number = IntegerField('Угадайте число (1–10)', validators=[DataRequired(), NumberRange(min=1, max=10)])
    submit = SubmitField('Угадать')

class MinesStartForm(FlaskForm):
    bet_amount = IntegerField('Сумма ставки (баллы)', validators=[DataRequired(), NumberRange(min=1)])
    mine_count = IntegerField('Количество мин (1–24)', validators=[DataRequired(), NumberRange(min=1, max=24)])
    submit = SubmitField('Начать игру')