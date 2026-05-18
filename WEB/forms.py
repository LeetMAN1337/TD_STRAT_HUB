from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from models import User, Tag
import re


def no_profanity(form, field):
    profanity_list = [
        'блядь', 'блять', 'сука', 'пизда', 'пиздец', 'хуй', 'хуя', 'хуе', 'хуё',
        'ебать', 'ебаный', 'ёбаный', 'ебан', 'ёбан', 'нахуй', 'похуй', 'заебал',
        'заебись', 'охуел', 'ахуел', 'охуеть', 'ахуеть', 'пиздеж', 'пиздец',
        'мразь', 'сволочь', 'гандон', 'мудак', 'долбоёб', 'долбоеб', 'уебок',
        'уёбок', 'пидор', 'пидорас', 'пидр', 'чмо', 'чмырь', 'шлюха', 'проститутка',
        'ебло', 'ебал', 'трахать', 'трахнуть', 'выебать', 'выебал', 'сосать',
        'отсос', 'член', 'жопа', 'говно', 'дерьмо', 'срать', 'сраный', 'ссаный',
        'ссать', 'блевать', 'блевот', 'урод', 'уродина', 'дебил', 'даун',
        'идиот', 'тупица', 'кретин', 'шизик', 'шизоид', 'псих', 'психопат',
        'еблан', 'уёбище', 'ебасос', 'хуйло', 'залупа', 'пенис', 'гей',
        'fuck', 'shit', 'bitch', 'ass', 'asshole', 'dick', 'cock', 'pussy',
        'cunt', 'bastard', 'damn', 'hell', 'crap', 'douche', 'douchebag',
        'motherfucker', 'twat', 'wanker', 'arse', 'arsehole', 'bollocks',
        'bugger', 'tosser', 'wank', 'prick', 'knob', 'knobhead', 'bellend',
        'dickhead', 'shithead', 'fucker', 'fucking', 'fucked', 'cockhead',
        'piss', 'pissed', 'slut', 'whore', 'nigger', 'nigga', 'faggot', 'fag',
        'retard', 'moron', 'dumbass', 'jackass', 'dipshit', 'bullshit',
        'arsehole', 'balls', 'bollocks', 'crap', 'dildo', 'dumb', 'idiot',
        'jerk', 'loser', 'scum', 'sucker', 'suck', 'tits', 'tit', 'boobs',
        'boob', 'viagra', 'porn', 'porno', 'sex', 'sexual', 'semen', 'cum',
        'penis', 'vagina', 'clitoris', 'anal', 'anus', 'orgasm', 'masturbat',
        'hentai', 'xxx', 'xrated', 'milf', 'dilf', 'nsfw', 'escort', 'stripper',
        'hooker', 'prostitute', 'bdsm', 'fetish', 'kinky', 'bondage', 'dominatrix',
        'incest', 'rape', 'rapist', 'molest', 'pedo', 'pedophile', 'zoophilia',
        'necrophilia', 'coprophilia', 'urophilia'
    ]
    text = field.data.lower() if field.data else ''
    text_clean = re.sub(r'[^а-яёa-z]', '', text)
    for word in profanity_list:
        if word in text_clean:
            raise ValidationError('Текст содержит недопустимую лексику. Пожалуйста, исправьте.')


class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=20), no_profanity])
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
    title = StringField('Название стратегии', validators=[DataRequired(), no_profanity])
    game = StringField('Название игры', validators=[DataRequired(), no_profanity])
    description = TextAreaField('Описание', validators=[DataRequired(), no_profanity])
    image = FileField('Скриншот (необязательно)', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Только изображения!')
    ])
    tags = SelectMultipleField('Теги', coerce=int)
    submit = SubmitField('Опубликовать')

class CommentForm(FlaskForm):
    text = TextAreaField('Комментарий', validators=[DataRequired(), Length(min=1, max=500), no_profanity])
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