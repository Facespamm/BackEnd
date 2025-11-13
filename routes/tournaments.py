"""
Маршруты для управления турнирами
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from utils.security import admin_required
from models.tournament import Tournament
from models.category import Category
from models.athlete import Athlete
from database.db import db

tournaments_bp = Blueprint('tournaments', __name__)

@tournaments_bp.route('/')
@admin_required
def list_tournaments():
    """Список турниров"""
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')

    query = Tournament.query

    if status_filter:
        query = query.filter_by(status=status_filter)

    if search:
        query = query.filter(Tournament.name.ilike(f'%{search}%'))

    tournaments = query.order_by(Tournament.start_date.desc()).all()

    return render_template(
        'admin/tournaments/list.html',
        tournaments=tournaments,
        status_filter=status_filter,
        search=search
    )

@tournaments_bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create_tournament():
    """Создание турнира"""
    from utils.forms import TournamentForm
    from utils.validators import validate_tournament_data

    form = TournamentForm()

    if form.validate_on_submit():
        # Валидация данных
        errors = validate_tournament_data(request.form)

        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            # Создание турнира
            tournament = Tournament(
                name=form.name.data,
                description=form.description.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                registration_deadline=form.registration_deadline.data,
                venue=form.venue.data,
                address=form.address.data,
                city=form.city.data,
                country=form.country.data,
                max_athletes=form.max_athletes.data,
                tatami_count=form.tatami_count.data,
                fight_duration=form.fight_duration.data,
                golden_score_duration=form.golden_score_duration.data,
                organizer=form.organizer.data,
                chief_referee=form.chief_referee.data,
                contact_phone=form.contact_phone.data,
                contact_email=form.contact_email.data
            )

            if tournament.save():
                flash(f'Турнир "{tournament.name}" успешно создан', 'success')
                return redirect(url_for('tournaments.manage_tournament', tournament_id=tournament.id))
            else:
                flash('Ошибка при создании турнира', 'danger')

    return render_template('admin/tournaments/create.html', form=form)

@tournaments_bp.route('/<int:tournament_id>/manage')
@admin_required
def manage_tournament(tournament_id):
    """Управление турниром"""
    tournament = Tournament.query.get_or_404(tournament_id)

    # Статистика турнира
    stats = {
        'total_athletes': tournament.athletes_count,
        'total_categories': len(tournament.categories),
        'completed_fights': tournament.completed_fights_count,
        'total_fights': tournament.total_fights_count,
        'progress_percentage': tournament.progress_percentage
    }

    return render_template(
        'admin/tournaments/manage.html',
        tournament=tournament,
        stats=stats
    )

@tournaments_bp.route('/<int:tournament_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_tournament(tournament_id):
    """Редактирование турнира"""
    from utils.forms import TournamentForm

    tournament = Tournament.query.get_or_404(tournament_id)
    form = TournamentForm(obj=tournament)

    if form.validate_on_submit():
        form.populate_obj(tournament)

        if tournament.save():
            flash('Турнир успешно обновлен', 'success')
            return redirect(url_for('tournaments.manage_tournament', tournament_id=tournament.id))
        else:
            flash('Ошибка при обновлении турнира', 'danger')

    return render_template('admin/tournaments/create.html', form=form, tournament=tournament, action='edit')

@tournaments_bp.route('/<int:tournament_id>/delete', methods=['POST'])
@admin_required
def delete_tournament(tournament_id):
    """Удаление турнира"""
    tournament = Tournament.query.get_or_404(tournament_id)

    # Можно удалять только запланированные турниры
    if tournament.status != 'PLANNED':
        flash('Можно удалять только запланированные турниры', 'danger')
        return redirect(url_for('tournaments.list_tournaments'))

    if tournament.delete():
        flash('Турнир успешно удален', 'success')
    else:
        flash('Ошибка при удалении турнира', 'danger')

    return redirect(url_for('tournaments.list_tournaments'))

@tournaments_bp.route('/<int:tournament_id>/categories')
@admin_required
def tournament_categories(tournament_id):
    """Управление категориями турнира"""
    tournament = Tournament.query.get_or_404(tournament_id)

    return render_template(
        'admin/tournaments/categories.html',
        tournament=tournament
    )

@tournaments_bp.route('/<int:tournament_id>/categories/add', methods=['GET', 'POST'])
@admin_required
def add_category(tournament_id):
    """Добавление категории в турнир"""
    from utils.forms import CategoryForm
    from utils.validators import validate_category_data

    tournament = Tournament.query.get_or_404(tournament_id)
    form = CategoryForm()

    if form.validate_on_submit():
        # Валидация данных
        errors = validate_category_data(request.form)

        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            # Создание категории
            category = Category(
                tournament_id=tournament_id,
                name=form.name.data,
                gender=form.gender.data,
                min_weight=form.min_weight.data,
                max_weight=form.max_weight.data,
                min_age=form.min_age.data,
                max_age=form.max_age.data
            )

            if category.save():
                flash(f'Категория "{category.name}" успешно создана', 'success')
                return redirect(url_for('tournaments.tournament_categories', tournament_id=tournament_id))
            else:
                flash('Ошибка при создании категории', 'danger')

    return render_template('admin/tournaments/category_form.html', form=form, tournament=tournament, action='add')

@tournaments_bp.route('/<int:tournament_id>/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(tournament_id, category_id):
    """Редактирование категории"""
    from utils.forms import CategoryForm

    tournament = Tournament.query.get_or_404(tournament_id)
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        form.populate_obj(category)

        if category.save():
            flash('Категория успешно обновлена', 'success')
            return redirect(url_for('tournaments.tournament_categories', tournament_id=tournament_id))
        else:
            flash('Ошибка при обновлении категории', 'danger')

    return render_template('admin/tournaments/category_form.html', form=form, tournament=tournament, category=category, action='edit')

@tournaments_bp.route('/<int:tournament_id>/categories/<int:category_id>/delete', methods=['POST'])
@admin_required
def delete_category(tournament_id, category_id):
    """Удаление категории"""
    category = Category.query.get_or_404(category_id)

    if category.delete():
        flash('Категория успешно удалена', 'success')
    else:
        flash('Ошибка при удалении категории', 'danger')

    return redirect(url_for('tournaments.tournament_categories', tournament_id=tournament_id))

@tournaments_bp.route('/<int:tournament_id>/start')
@admin_required
def start_tournament(tournament_id):
    """Начало турнира"""
    tournament = Tournament.query.get_or_404(tournament_id)

    if tournament.status != 'BRACKETS':
        flash('Турнир должен быть в стадии формирования сеток', 'danger')
        return redirect(url_for('tournaments.manage_tournament', tournament_id=tournament_id))

    tournament.status = 'LIVE'

    if tournament.save():
        flash('Турнир начат!', 'success')
    else:
        flash('Ошибка при запуске турнира', 'danger')

    return redirect(url_for('tournaments.manage_tournament', tournament_id=tournament_id))

@tournaments_bp.route('/<int:tournament_id>/complete')
@admin_required
def complete_tournament(tournament_id):
    """Завершение турнира"""
    tournament = Tournament.query.get_or_404(tournament_id)

    if tournament.status != 'LIVE':
        flash('Турнир должен быть активен', 'danger')
        return redirect(url_for('tournaments.manage_tournament', tournament_id=tournament_id))

    tournament.status = 'COMPLETED'

    if tournament.save():
        flash('Турнир завершен!', 'success')
    else:
        flash('Ошибка при завершении турнира', 'danger')

    return redirect(url_for('tournaments.manage_tournament', tournament_id=tournament_id))

@tournaments_bp.route('/<int:tournament_id>/registrations')
@admin_required
def tournament_registrations(tournament_id):
    """Регистрации на турнир"""
    tournament = Tournament.query.get_or_404(tournament_id)

    # Участники по категориям
    categories_with_athletes = []
    for category in tournament.categories:
        categories_with_athletes.append({
            'category': category,
            'athletes': category.athletes
        })

    return render_template(
        'admin/tournaments/registrations.html',
        tournament=tournament,
        categories_with_athletes=categories_with_athletes
    )

@tournaments_bp.route('/<int:tournament_id>/registrations/add_athlete', methods=['POST'])
@admin_required
def add_athlete_to_tournament(tournament_id):
    """Добавление участника в турнир"""
    tournament = Tournament.query.get_or_404(tournament_id)
    athlete_id = request.form.get('athlete_id')
    category_id = request.form.get('category_id')

    if not athlete_id or not category_id:
        flash('Необходимо выбрать участника и категорию', 'danger')
        return redirect(url_for('tournaments.tournament_registrations', tournament_id=tournament_id))

    athlete = Athlete.query.get(athlete_id)
    category = Category.query.get(category_id)

    if not athlete or not category:
        flash('Участник или категория не найдены', 'danger')
        return redirect(url_for('tournaments.tournament_registrations', tournament_id=tournament_id))

    # Проверяем, не зарегистрирован ли уже участник в этой категории
    if athlete in category.athletes:
        flash('Участник уже зарегистрирован в этой категории', 'warning')
        return redirect(url_for('tournaments.tournament_registrations', tournament_id=tournament_id))

    # Добавляем участника в категорию
    category.add_athlete(athlete)

    flash(f'Участник {athlete.full_name} добавлен в категорию {category.name}', 'success')
    return redirect(url_for('tournaments.tournament_registrations', tournament_id=tournament_id))