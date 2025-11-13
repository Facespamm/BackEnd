"""
Формы WTForms для системы
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateField, IntegerField, FloatField, BooleanField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, ValidationError
from datetime import date, datetime

class AthleteForm(FlaskForm):
    """Форма участника"""
    first_name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(min=2, max=50)])
    middle_name = StringField('Отчество', validators=[Optional(), Length(max=50)])
    birth_date = DateField('Дата рождения', validators=[DataRequired()])
    gender = SelectField('Пол', choices=[('MALE', 'Мужской'), ('FEMALE', 'Женский')], validators=[DataRequired()])

    club_id = SelectField('Клуб', coerce=int, validators=[Optional()])
    rank = SelectField('Разряд', choices=[
        ('', 'Не указан'),
        ('6KYU', '6 кю (белый)'),
        ('5KYU', '5 кю (желтый)'),
        ('4KYU', '4 кю (оранжевый)'),
        ('3KYU', '3 кю (зеленый)'),
        ('2KYU', '2 кю (синий)'),
        ('1KYU', '1 кю (коричневый)'),
        ('1DAN', '1 дан (черный)'),
        ('2DAN', '2 дан (черный)'),
        ('3DAN', '3 дан (черный)'),
        ('4DAN', '4 дан (черный)'),
        ('5DAN', '5 дан (черный)')
    ], validators=[Optional()])

    license_number = StringField('Номер лицензии', validators=[Optional(), Length(max=50)])
    phone = StringField('Телефон', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=100)])

    medical_check = BooleanField('Медицинский допуск')
    insurance_number = StringField('Номер страховки', validators=[Optional(), Length(max=50)])

    def validate_birth_date(self, field):
        if field.data and field.data > date.today():
            raise ValidationError('Дата рождения не может быть в будущем')

        age = date.today().year - field.data.year
        if age < 4:
            raise ValidationError('Участник должен быть старше 4 лет')
        if age > 100:
            raise ValidationError('Проверьте дату рождения')

class TournamentForm(FlaskForm):
    """Форма турнира"""
    name = StringField('Название турнира', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Описание', validators=[Optional()])

    start_date = DateField('Дата начала', validators=[DataRequired()])
    end_date = DateField('Дата окончания', validators=[DataRequired()])
    registration_deadline = DateField('Дедлайн регистрации', validators=[Optional()])

    venue = StringField('Место проведения', validators=[DataRequired(), Length(max=200)])
    address = TextAreaField('Адрес', validators=[Optional()])
    city = StringField('Город', validators=[Optional(), Length(max=50)])
    country = StringField('Страна', validators=[Optional(), Length(max=50)])

    max_athletes = IntegerField('Макс. участников', validators=[Optional(), NumberRange(min=0)], default=0)
    tatami_count = IntegerField('Количество татами', validators=[DataRequired(), NumberRange(min=1, max=20)], default=1)
    fight_duration = IntegerField('Длительность схватки (сек)', validators=[DataRequired(), NumberRange(min=60, max=600)], default=300)
    golden_score_duration = IntegerField('Длительность золотого скора (сек)', validators=[DataRequired(), NumberRange(min=60, max=300)], default=180)

    organizer = StringField('Организатор', validators=[Optional(), Length(max=100)])
    chief_referee = StringField('Главный судья', validators=[Optional(), Length(max=100)])
    contact_phone = StringField('Контактный телефон', validators=[Optional(), Length(max=20)])
    contact_email = StringField('Контактный email', validators=[Optional(), Email(), Length(max=100)])

    def validate_start_date(self, field):
        if field.data and field.data < date.today():
            raise ValidationError('Дата начала не может быть в прошлом')

    def validate_end_date(self, field):
        if self.start_date.data and field.data and field.data < self.start_date.data:
            raise ValidationError('Дата окончания не может быть раньше даты начала')

class CategoryForm(FlaskForm):
    """Форма весовой категории"""
    name = StringField('Название категории', validators=[DataRequired(), Length(max=50)])
    gender = SelectField('Пол', choices=[('MALE', 'Мужская'), ('FEMALE', 'Женская')], validators=[DataRequired()])

    min_weight = FloatField('Минимальный вес (кг)', validators=[Optional(), NumberRange(min=20, max=200)])
    max_weight = FloatField('Максимальный вес (кг)', validators=[Optional(), NumberRange(min=20, max=200)])

    min_age = IntegerField('Минимальный возраст', validators=[Optional(), NumberRange(min=4, max=100)])
    max_age = IntegerField('Максимальный возраст', validators=[Optional(), NumberRange(min=4, max=100)])

    def validate_min_weight(self, field):
        if field.data and self.max_weight.data and field.data >= self.max_weight.data:
            raise ValidationError('Минимальный вес должен быть меньше максимального')

    def validate_min_age(self, field):
        if field.data and self.max_age.data and field.data >= self.max_age.data:
            raise ValidationError('Минимальный возраст должен быть меньше максимального')

class UserForm(FlaskForm):
    """Форма пользователя"""
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Пароль', validators=[Optional(), Length(min=4)])
    name = StringField('Полное имя', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=100)])
    phone = StringField('Телефон', validators=[Optional(), Length(max=20)])

    role = SelectField('Роль', choices=[
        ('ADMIN', 'Администратор'),
        ('REFEREE', 'Судья'),
        ('SCOREBOARD', 'Оператор табло'),
        ('VIEWER', 'Зритель')
    ], validators=[DataRequired()])

    referee_level = SelectField('Уровень судьи', choices=[
        ('', 'Не указан'),
        ('NATIONAL_3', 'Национальный 3 категории'),
        ('NATIONAL_2', 'Национальный 2 категории'),
        ('NATIONAL_1', 'Национальный 1 категории'),
        ('CONTINENTAL_C', 'Континентальный C'),
        ('CONTINENTAL_B', 'Континентальный B'),
        ('CONTINENTAL_A', 'Континентальный A')
    ], validators=[Optional()])

    tatami_assigned = IntegerField('Назначенный татами', validators=[Optional(), NumberRange(min=1, max=20)])

class WeighingForm(FlaskForm):
    """Форма взвешивания"""
    weight = FloatField('Вес (кг)', validators=[DataRequired(), NumberRange(min=20, max=200)])
    notes = TextAreaField('Заметки', validators=[Optional()])

class FightForm(FlaskForm):
    """Форма схватки"""
    white_athlete_id = SelectField('Белый участник', coerce=int, validators=[Optional()])
    blue_athlete_id = SelectField('Синий участник', coerce=int, validators=[Optional()])

    tatami = IntegerField('Татами', validators=[DataRequired(), NumberRange(min=1, max=20)], default=1)
    round_number = IntegerField('Раунд', validators=[DataRequired(), NumberRange(min=1, max=10)], default=1)
    fight_number = IntegerField('Номер схватки', validators=[Optional()])

    scheduled_time = DateTimeField('Запланированное время', validators=[Optional()], format='%Y-%m-%d %H:%M')

    main_referee = StringField('Главный судья', validators=[Optional(), Length(max=100)])
    judge1 = StringField('Судья 1', validators=[Optional(), Length(max=100)])
    judge2 = StringField('Судья 2', validators=[Optional(), Length(max=100)])

class ResultForm(FlaskForm):
    """Форма результата схватки"""
    winner_id = SelectField('Победитель', coerce=int, validators=[DataRequired()])
    victory_type = SelectField('Тип победы', choices=[
        ('IPPON', 'Иппон'),
        ('WAZAARI_AWASETE_IPPON', 'Ваза-ари авасетэ иппон'),
        ('WAZAARI', 'Ваза-ари'),
        ('SHIDO', 'Победа по штрафам'),
        ('HANSOKU_MAKE', 'Хансоку-маке'),
        ('FUSEN_GACHI', 'Фусэн-гати (неявка)'),
        ('KIKEN_GACHI', 'Кикэн-гати (отказ)')
    ], validators=[DataRequired()])

    details = TextAreaField('Детали', validators=[Optional()])
    technique_used = StringField('Использованная техника', validators=[Optional(), Length(max=100)])

class LoginForm(FlaskForm):
    """Форма входа"""
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=4)])

class RefereeLoginForm(FlaskForm):
    """Форма входа для судей"""
    tatami = IntegerField('Татами', validators=[DataRequired(), NumberRange(min=1, max=20)])
    code = StringField('Код доступа', validators=[DataRequired(), Length(min=4, max=10)])

class SearchForm(FlaskForm):
    """Форма поиска"""
    query = StringField('Поиск', validators=[DataRequired(), Length(min=2, max=100)])
    search_type = SelectField('Тип поиска', choices=[
        ('athletes', 'Участники'),
        ('clubs', 'Клубы'),
        ('tournaments', 'Турниры')
    ], default='athletes')