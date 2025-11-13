"""
Основные маршруты приложения
"""

from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from utils.security import login_required, get_current_user, login_user, logout_user
from utils.forms import LoginForm
from models.user import User

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Главная страница"""
    return redirect(url_for('public.index'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    # Если пользователь уже авторизован, перенаправляем на dashboard
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Поиск пользователя
        user = User.query.filter_by(username=username, is_active=True).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'Добро пожаловать, {user.name}!', 'success')

            # Перенаправление в зависимости от роли
            if user.role == 'ADMIN':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'REFEREE':
                return redirect(url_for('referee.dashboard'))
            else:
                return redirect(url_for('main.dashboard'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('login.html', form=form)

@main_bp.route('/logout')
def logout():
    """Выход из системы"""
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('main.login'))

@main_bp.route('/dashboard')
@login_required()
def dashboard():
    """Панель управления (общая)"""
    user = get_current_user()

    if user.role == 'ADMIN':
        return redirect(url_for('admin.dashboard'))
    elif user.role == 'REFEREE':
        return redirect(url_for('referee.dashboard'))
    elif user.role == 'SCOREBOARD':
        return redirect(url_for('scoreboard.main'))
    else:
        return redirect(url_for('public.index'))

@main_bp.route('/profile')
@login_required()
def profile():
    """Профиль пользователя"""
    user = get_current_user()
    return render_template('profile.html', user=user)

@main_bp.route('/settings')
@login_required()
def settings():
    """Настройки системы"""
    user = get_current_user()

    if user.role != 'ADMIN':
        flash('Недостаточно прав для доступа к настройкам', 'danger')
        return redirect(url_for('main.dashboard'))

    return render_template('settings.html')

@main_bp.route('/help')
def help():
    """Справка и помощь"""
    return render_template('help.html')

@main_bp.errorhandler(404)
def not_found(error):
    """Обработчик 404 ошибки"""
    return render_template('error.html', error=error), 404

@main_bp.errorhandler(500)
def internal_error(error):
    """Обработчик 500 ошибки"""
    return render_template('error.html', error=error), 500