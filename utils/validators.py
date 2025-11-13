"""
Валидаторы данных для системы
"""

import re
from datetime import datetime, date
from flask import flash

def validate_athlete_data(data):
    """
    Валидация данных участника
    """
    errors = []

    # Проверка обязательных полей
    required_fields = ['first_name', 'last_name', 'birth_date', 'gender']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"Поле '{field}' обязательно для заполнения")

    # Проверка имени и фамилии
    if data.get('first_name') and len(data['first_name']) < 2:
        errors.append("Имя должно содержать минимум 2 символа")

    if data.get('last_name') and len(data['last_name']) < 2:
        errors.append("Фамилия должна содержать минимум 2 символа")

    # Проверка даты рождения
    if data.get('birth_date'):
        try:
            birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
            if birth_date > date.today():
                errors.append("Дата рождения не может быть в будущем")

            # Проверка возраста
            age = date.today().year - birth_date.year
            if age < 4:
                errors.append("Участник должен быть старше 4 лет")
            if age > 100:
                errors.append("Проверьте дату рождения")

        except ValueError:
            errors.append("Неверный формат даты рождения")

    # Проверка email
    if data.get('email'):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            errors.append("Неверный формат email")

    # Проверка телефона
    if data.get('phone'):
        phone_pattern = r'^[\+]?[0-9\s\-\(\)]{10,15}$'
        if not re.match(phone_pattern, data['phone'].replace(' ', '')):
            errors.append("Неверный формат телефона")

    return errors

def validate_tournament_data(data):
    """
    Валидация данных турнира
    """
    errors = []

    # Проверка обязательных полей
    required_fields = ['name', 'start_date', 'end_date', 'venue']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"Поле '{field}' обязательно для заполнения")

    # Проверка дат
    if data.get('start_date') and data.get('end_date'):
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()

            if start_date > end_date:
                errors.append("Дата начала не может быть позже даты окончания")

            if start_date < date.today():
                errors.append("Дата начала не может быть в прошлом")

        except ValueError:
            errors.append("Неверный формат даты")

    # Проверка количества татами
    if data.get('tatami_count'):
        try:
            tatami_count = int(data['tatami_count'])
            if tatami_count < 1 or tatami_count > 20:
                errors.append("Количество татами должно быть от 1 до 20")
        except ValueError:
            errors.append("Неверный формат количества татами")

    # Проверка email
    if data.get('contact_email'):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['contact_email']):
            errors.append("Неверный формат контактного email")

    return errors

def validate_fight_data(data):
    """
    Валидация данных схватки
    """
    errors = []

    # Проверка участников
    if not data.get('white_athlete_id') and not data.get('blue_athlete_id'):
        errors.append("Должен быть хотя бы один участник")

    # Проверка татами
    if data.get('tatami'):
        try:
            tatami = int(data['tatami'])
            if tatami < 1 or tatami > 20:
                errors.append("Номер татами должен быть от 1 до 20")
        except ValueError:
            errors.append("Неверный формат номера татами")

    # Проверка раунда
    if data.get('round_number'):
        try:
            round_number = int(data['round_number'])
            if round_number < 1 or round_number > 10:
                errors.append("Номер раунда должен быть от 1 до 10")
        except ValueError:
            errors.append("Неверный формат номера раунда")

    return errors

def validate_weighing_data(data):
    """
    Валидация данных взвешивания
    """
    errors = []

    if not data.get('weight'):
        errors.append("Вес обязателен для заполнения")
    else:
        try:
            weight = float(data['weight'])
            if weight < 20 or weight > 200:
                errors.append("Вес должен быть от 20 до 200 кг")
        except ValueError:
            errors.append("Неверный формат веса")

    return errors

def validate_user_data(data):
    """
    Валидация данных пользователя
    """
    errors = []

    required_fields = ['username', 'name', 'role']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"Поле '{field}' обязательно для заполнения")

    if data.get('username'):
        username = data['username']
        if len(username) < 3:
            errors.append("Имя пользователя должно содержать минимум 3 символа")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append("Имя пользователя может содержать только буквы, цифры и подчеркивания")

    if data.get('password') and len(data['password']) < 4:
        errors.append("Пароль должен содержать минимум 4 символа")

    if data.get('email'):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            errors.append("Неверный формат email")

    return errors

def validate_category_data(data):
    """
    Валидация данных весовой категории
    """
    errors = []

    if not data.get('name'):
        errors.append("Название категории обязательно")

    if not data.get('gender'):
        errors.append("Пол обязателен для категории")

    # Проверка весовых ограничений
    min_weight = data.get('min_weight')
    max_weight = data.get('max_weight')

    if min_weight and max_weight:
        try:
            min_w = float(min_weight)
            max_w = float(max_weight)
            if min_w >= max_w:
                errors.append("Минимальный вес должен быть меньше максимального")
        except ValueError:
            errors.append("Неверный формат веса")

    # Проверка возрастных ограничений
    min_age = data.get('min_age')
    max_age = data.get('max_age')

    if min_age and max_age:
        try:
            min_a = int(min_age)
            max_a = int(max_age)
            if min_a >= max_a:
                errors.append("Минимальный возраст должен быть меньше максимального")
        except ValueError:
            errors.append("Неверный формат возраста")

    return errors