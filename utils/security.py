"""
Функции безопасности и аутентификации
"""

import hashlib
import secrets
import string
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
from flask_jwt_extended import get_jwt


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

def role_required(*roles):
    def decorated_function(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role')

            if user_role not in roles:
                return jsonify({
                    'message':'Доступ запришен'
                }), 403
            return fn(*args, **kwargs)
        return wrapper
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