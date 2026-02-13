"""
Функции безопасности и аутентификации
"""

import hashlib
import secrets
import string
from functools import wraps
from flask import session, redirect, url_for, flash, request

def generate_referee_code(length=6):
    """
    Генерация кода для судей
    """
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def generate_api_key():
    """
    Генерация API ключа
    """
    return secrets.token_urlsafe(32)

def login_required(role=None):
    """
    Декоратор для проверки аутентификации и роли
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Требуется авторизация', 'warning')
                return redirect(url_for('main.login'))

            # Проверка роли если указана
            if role and session.get('user_role') != role:
                flash('Недостаточно прав', 'danger')
                return redirect(url_for('main.dashboard'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    Декоратор для проверки прав администратора
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Требуется авторизация', 'warning')
            return redirect(url_for('main.login'))

        if session.get('user_role') != 'ADMIN':
            flash('Требуются права администратора', 'danger')
            return redirect(url_for('main.dashboard'))

        return f(*args, **kwargs)
    return decorated_function

def referee_required(f):
    """
    Декоратор для проверки прав судьи
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Требуется авторизация', 'warning')
            return redirect(url_for('referee.login'))

        if session.get('user_role') not in ['ADMIN', 'REFEREE']:
            flash('Требуются права судьи', 'danger')
            return redirect(url_for('main.dashboard'))

        return f(*args, **kwargs)
    return decorated_function

def scoreboard_required(f):
    """
    Декоратор для проверки прав доступа к табло
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Для табло может быть публичный доступ
            if request.endpoint and 'scoreboard' in request.endpoint:
                return f(*args, **kwargs)
            flash('Требуется авторизация', 'warning')
            return redirect(url_for('main.login'))

        if session.get('user_role') not in ['ADMIN', 'SCOREBOARD', 'REFEREE']:
            flash('Недостаточно прав для доступа к табло', 'danger')
            return redirect(url_for('main.dashboard'))

        return f(*args, **kwargs)
    return decorated_function