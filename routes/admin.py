"""
Административные маршруты
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from utils.security import admin_required, get_current_user
from models.tournament import Tournament
from models.athlete import Athlete
from models.club import Club
from models.user import User
from models.fight import Fight
from database.db import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@admin_required
def dashboard():
    """Административная панель"""
    # Статистика для dashboard
    stats = {
        'total_tournaments': Tournament.query.count(),
        'active_tournaments': Tournament.query.filter(
            Tournament.status.in_(['REGISTRATION', 'WEIGHING', 'BRACKETS', 'LIVE'])
        ).count(),
        'total_athletes': Athlete.query.filter_by(is_active=True).count(),
        'total_clubs': Club.query.filter_by(is_active=True).count(),
        'total_users': User.query.filter_by(is_active=True).count(),
        'live_fights': Fight.query.filter_by(status='LIVE').count()
    }

    # Последние турниры
    recent_tournaments = Tournament.query.order_by(
        Tournament.created_at.desc()
    ).limit(5).all()

    # Активные турниры
    active_tournaments = Tournament.query.filter(
        Tournament.status.in_(['LIVE', 'BRACKETS'])
    ).order_by(Tournament.start_date).all()

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_tournaments=recent_tournaments,
        active_tournaments=active_tournaments
    )

@admin_bp.route('/users')
@admin_required
def users():
    """Управление пользователями"""
    users_list = User.query.filter_by(is_active=True).order_by(User.username).all()
    return render_template('admin/users.html', users=users_list)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    """Добавление пользователя"""
    from utils.forms import UserForm
    from utils.validators import validate_user_data

    form = UserForm()

    # Заполняем выбор клубов
    form.club_id.choices = [(0, '-- Выберите клуб --')] + [
        (club.id, club.name) for club in Club.query.filter_by(is_active=True).order_by(Club.name).all()
    ]

    if form.validate_on_submit():
        # Валидация данных
        errors = validate_user_data(request.form)

        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            # Создание пользователя
            user = User(
                username=form.username.data,
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                role=form.role.data,
                referee_level=form.referee_level.data,
                tatami_assigned=form.tatami_assigned.data
            )

            if form.password.data:
                user.set_password(form.password.data)
            else:
                user.set_password('password')  # Дефолтный пароль

            if user.save():
                flash(f'Пользователь {user.username} успешно создан', 'success')
                return redirect(url_for('admin.users'))
            else:
                flash('Ошибка при создании пользователя', 'danger')

    return render_template('admin/user_form.html', form=form, action='add')

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Редактирование пользователя"""
    from utils.forms import UserForm

    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)

    if form.validate_on_submit():
        user.username = form.username.data
        user.name = form.name.data
        user.email = form.email.data
        user.phone = form.phone.data
        user.role = form.role.data
        user.referee_level = form.referee_level.data
        user.tatami_assigned = form.tatami_assigned.data

        if form.password.data:
            user.set_password(form.password.data)

        if user.save():
            flash('Пользователь успешно обновлен', 'success')
            return redirect(url_for('admin.users'))
        else:
            flash('Ошибка при обновлении пользователя', 'danger')

    return render_template('admin/user_form.html', form=form, user=user, action='edit')

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Удаление пользователя"""
    user = User.query.get_or_404(user_id)

    # Нельзя удалить самого себя
    current_user = get_current_user()
    if user.id == current_user.id:
        flash('Нельзя удалить собственный аккаунт', 'danger')
        return redirect(url_for('admin.users'))

    user.is_active = False
    if user.save():
        flash('Пользователь успешно удален', 'success')
    else:
        flash('Ошибка при удалении пользователя', 'danger')

    return redirect(url_for('admin.users'))

@admin_bp.route('/clubs')
@admin_required
def clubs():
    """Управление клубами"""
    clubs_list = Club.query.filter_by(is_active=True).order_by(Club.name).all()
    return render_template('admin/clubs.html', clubs=clubs_list)

@admin_bp.route('/clubs/add', methods=['GET', 'POST'])
@admin_required
def add_club():
    """Добавление клуба"""
    from utils.forms import ClubForm

    form = ClubForm()

    if form.validate_on_submit():
        club = Club(
            name=form.name.data,
            short_name=form.short_name.data,
            city=form.city.data,
            country=form.country.data,
            address=form.address.data,
            phone=form.phone.data,
            email=form.email.data,
            website=form.website.data,
            coach_name=form.coach_name.data,
            founded_year=form.founded_year.data
        )

        if club.save():
            flash(f'Клуб {club.name} успешно создан', 'success')
            return redirect(url_for('admin.clubs'))
        else:
            flash('Ошибка при создании клуба', 'danger')

    return render_template('admin/club_form.html', form=form, action='add')

@admin_bp.route('/clubs/<int:club_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_club(club_id):
    """Редактирование клуба"""
    from utils.forms import ClubForm

    club = Club.query.get_or_404(club_id)
    form = ClubForm(obj=club)

    if form.validate_on_submit():
        form.populate_obj(club)

        if club.save():
            flash('Клуб успешно обновлен', 'success')
            return redirect(url_for('admin.clubs'))
        else:
            flash('Ошибка при обновлении клуба', 'danger')

    return render_template('admin/club_form.html', form=form, club=club, action='edit')

@admin_bp.route('/clubs/<int:club_id>/delete', methods=['POST'])
@admin_required
def delete_club(club_id):
    """Удаление клуба"""
    club = Club.query.get_or_404(club_id)
    club.is_active = False

    if club.save():
        flash('Клуб успешно удален', 'success')
    else:
        flash('Ошибка при удалении клуба', 'danger')

    return redirect(url_for('admin.clubs'))

@admin_bp.route('/system/stats')
@admin_required
def system_stats():
    """Статистика системы"""
    from services.result_calculator import ResultCalculator

    # Общая статистика
    stats = {
        'total_tournaments': Tournament.query.count(),
        'completed_tournaments': Tournament.query.filter_by(status='COMPLETED').count(),
        'total_athletes': Athlete.query.filter_by(is_active=True).count(),
        'total_fights': Fight.query.count(),
        'completed_fights': Fight.query.filter_by(status='COMPLETED').count()
    }

    # Статистика по техникам (из последних турниров)
    from services.ranking_service import RankingService
    ranking_service = RankingService()
    technique_stats = ranking_service.get_technique_statistics(limit=10)

    return render_template(
        'admin/system_stats.html',
        stats=stats,
        technique_stats=technique_stats
    )

@admin_bp.route('/system/backup')
@admin_required
def system_backup():
    """Резервное копирование"""
    # Здесь будет логика создания бэкапа
    flash('Функция резервного копирования в разработке', 'info')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/api/quick_stats')
@admin_required
def quick_stats():
    """API для быстрой статистики (AJAX)"""
    stats = {
        'live_tournaments': Tournament.query.filter_by(status='LIVE').count(),
        'live_fights': Fight.query.filter_by(status='LIVE').count(),
        'scheduled_fights': Fight.query.filter_by(status='SCHEDULED').count(),
        'total_athletes': Athlete.query.filter_by(is_active=True).count()
    }

    return jsonify(stats)