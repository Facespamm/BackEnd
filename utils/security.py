"""
Функции безопасности и аутентификации
"""

import hashlib
import secrets
import string
from functools import wraps
from flask import session, redirect, url_for, flash, request

def hash_password(password):
    """
    Хеширование пароля с солью
    """
    salt = 'judo_tournament_salt_2024'
    return hashlib.sha256((password + salt).encode()).hexdigest()

def check_password(password_hash, password):
    """
    Проверка пароля
    """
    return password_hash == hash_password(password)

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

def get_current_user():
    """
    Получить текущего пользователя из сессии
    """
    from models.user import User
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def login_user(user):
    """
    Вход пользователя в систему
    """
    session['user_id'] = user.id
    session['user_username'] = user.username
    session['user_name'] = user.name
    session['user_role'] = user.role
    session['user_tatami'] = user.tatami_assigned
    session.permanent = True

def logout_user():
    """
    Выход пользователя из системы
    """
    session.clear()

def check_tatami_access(tatami_number):
    """
    Проверка доступа судьи к татами
    """
    user = get_current_user()
    if not user:
        return False

    # Админы имеют доступ ко всем татами
    if user.is_admin:
        return True

    # Судьи имеют доступ только к назначенным татами
    if user.is_referee and user.tatami_assigned:
        return user.tatami_assigned == tatami_number

    return False

def generate_password(length=8):
    """
    Генерация случайного пароля
    """
    characters = string.ascii_letters + string.digits + '!@#$%'
    return ''.join(secrets.choice(characters) for _ in range(length))

def validate_session():
    """
    Валидация сессии пользователя
    """
    if 'user_id' not in session:
        return False

    from models.user import User
    user = User.query.get(session['user_id'])
    if not user or not user.is_active:
        logout_user()
        return False

    return True

def require_tournament_access(tournament_id):
    """
    Декоратор для проверки доступа к турниру
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not validate_session():
                flash('Требуется авторизация', 'warning')
                return redirect(url_for('main.login'))

            from models.tournament import Tournament
            tournament = Tournament.query.get(tournament_id)

            if not tournament:
                flash('Турнир не найден', 'danger')
                return redirect(url_for('admin.tournaments'))

            # Админы имеют полный доступ
            user = get_current_user()
            if user.is_admin:
                return f(*args, **kwargs)

            # Для других ролей проверяем статус турнира
            if tournament.status in ['LIVE', 'COMPLETED']:
                return f(*args, **kwargs)

            flash('Доступ к этому турниру ограничен', 'danger')
            return redirect(url_for('main.dashboard'))

        return decorated_function
    return decorator