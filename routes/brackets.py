"""
Маршруты для управления турнирными сетками
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from utils.security import admin_required
from models.tournament import Tournament
from models.bracket import Bracket
from models.category import Category
from services.bracket_generator import BracketGenerator

brackets_bp = Blueprint('brackets', __name__)

@brackets_bp.route('/<int:tournament_id>')
@admin_required
def list_brackets(tournament_id):
    """Список сеток турнира"""
    tournament = Tournament.query.get_or_404(tournament_id)

    # Создаем сетки для категорий если их нет
    for category in tournament.categories:
        if not category.get_bracket():
            bracket = Bracket(
                tournament_id=tournament_id,
                category_id=category.id,
                name=f"Сетка {category.name}",
                bracket_type='SINGLE_ELIMINATION'
            )
            bracket.save()

    return render_template(
        'admin/brackets/list.html',
        tournament=tournament
    )

@brackets_bp.route('/<int:tournament_id>/generate/<int:category_id>')
@admin_required
def generate_bracket(tournament_id, category_id):
    """Генерация сетки для категории"""
    tournament = Tournament.query.get_or_404(tournament_id)
    category = Category.query.get_or_404(category_id)
    bracket = category.get_bracket()

    if not bracket:
        flash('Сетка не найдена', 'danger')
        return redirect(url_for('brackets.list_brackets', tournament_id=tournament_id))

    if len(category.athletes) < 2:
        flash('Для генерации сетки нужно минимум 2 участника', 'danger')
        return redirect(url_for('brackets.list_brackets', tournament_id=tournament_id))

    # Генерируем сетку
    generator = BracketGenerator(bracket)
    fights = generator.generate()

    if fights:
        flash(f'Сетка для категории "{category.name}" успешно сгенерирована. Создано {len(fights)} схваток.', 'success')
    else:
        flash('Ошибка при генерации сетки', 'danger')

    return redirect(url_for('brackets.view_bracket', tournament_id=tournament_id, category_id=category_id))

@brackets_bp.route('/<int:tournament_id>/view/<int:category_id>')
@admin_required
def view_bracket(tournament_id, category_id):
    """Просмотр сетки"""
    tournament = Tournament.query.get_or_404(tournament_id)
    category = Category.query.get_or_404(category_id)
    bracket = category.get_bracket()

    if not bracket:
        flash('Сетка не найдена', 'danger')
        return redirect(url_for('brackets.list_brackets', tournament_id=tournament_id))

    # Получаем схватки по раундам
    from models.fight import Fight
    fights_by_round = {}
    for fight in bracket.fights:
        if fight.round_number not in fights_by_round:
            fights_by_round[fight.round_number] = []
        fights_by_round[fight.round_number].append(fight)

    # Сортируем раунды
    rounds = sorted(fights_by_round.keys(), reverse=True)

    return render_template(
        'admin/brackets/view.html',
        tournament=tournament,
        category=category,
        bracket=bracket,
        fights_by_round=fights_by_round,
        rounds=rounds
    )

@brackets_bp.route('/<int:tournament_id>/edit/<int:category_id>')
@admin_required
def edit_bracket(tournament_id, category_id):
    """Редактирование сетки"""
    tournament = Tournament.query.get_or_404(tournament_id)
    category = Category.query.get_or_404(category_id)
    bracket = category.get_bracket()

    if not bracket:
        flash('Сетка не найдена', 'danger')
        return redirect(url_for('brackets.list_brackets', tournament_id=tournament_id))

    return render_template(
        'admin/brackets/edit.html',
        tournament=tournament,
        category=category,
        bracket=bracket
    )

@brackets_bp.route('/<int:tournament_id>/schedule')
@admin_required
def schedule_fights(tournament_id):
    """Планирование расписания схваток"""
    tournament = Tournament.query.get_or_404(tournament_id)

    # Получаем все незапланированные схватки
    from models.fight import Fight
    unscheduled_fights = Fight.query.filter_by(
        tournament_id=tournament_id,
        status='SCHEDULED',
        scheduled_time=None
    ).all()

    return render_template(
        'admin/brackets/schedule.html',
        tournament=tournament,
        unscheduled_fights=unscheduled_fights
    )

@brackets_bp.route('/<int:tournament_id>/auto_schedule', methods=['POST'])
@admin_required
def auto_schedule_fights(tournament_id):
    """Автоматическое планирование схваток"""
    tournament = Tournament.query.get_or_404(tournament_id)

    from datetime import datetime, timedelta
    from utils.helpers import schedule_fights

    # Получаем все незапланированные схватки
    from models.fight import Fight
    unscheduled_fights = Fight.query.filter_by(
        tournament_id=tournament_id,
        status='SCHEDULED',
        scheduled_time=None
    ).all()

    if not unscheduled_fights:
        flash('Нет незапланированных схваток', 'info')
        return redirect(url_for('brackets.schedule_fights', tournament_id=tournament_id))

    # Начальное время (следующий час)
    start_time = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    # Планируем схватки
    scheduled_fights = schedule_fights(
        unscheduled_fights,
        tournament.tatami_count,
        start_time,
        break_duration=300  # 5 минут перерыва
    )

    # Сохраняем
    for fight in scheduled_fights:
        fight.save()

    flash(f'Успешно запланировано {len(scheduled_fights)} схваток', 'success')
    return redirect(url_for('brackets.schedule_fights', tournament_id=tournament_id))

@brackets_bp.route('/<int:tournament_id>/update_fight_schedule', methods=['POST'])
@admin_required
def update_fight_schedule(tournament_id):
    """Обновление расписания схватки"""
    fight_id = request.form.get('fight_id')
    tatami = request.form.get('tatami')
    scheduled_time = request.form.get('scheduled_time')

    if not fight_id or not tatami or not scheduled_time:
        return jsonify({'success': False, 'error': 'Не все поля заполнены'})

    from models.fight import Fight
    fight = Fight.query.get(fight_id)

    if not fight or fight.tournament_id != tournament_id:
        return jsonify({'success': False, 'error': 'Схватка не найдена'})

    try:
        fight.tatami = int(tatami)
        fight.scheduled_time = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))

        if fight.save():
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Ошибка сохранения'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@brackets_bp.route('/<int:tournament_id>/api/bracket_data/<int:category_id>')
@admin_required
def api_bracket_data(tournament_id, category_id):
    """API данных сетки для визуализации"""
    category = Category.query.get_or_404(category_id)
    bracket = category.get_bracket()

    if not bracket:
        return jsonify({'error': 'Сетка не найдена'})

    # Формируем данные для визуализации сетки
    bracket_data = {
        'category': category.name,
        'status': bracket.status,
        'progress': bracket.progress_percentage,
        'fights': [],
        'athletes': []
    }

    # Данные участников
    for athlete in category.athletes:
        bracket_data['athletes'].append({
            'id': athlete.id,
            'name': athlete.full_name,
            'club': athlete.club.name if athlete.club else ''
        })

    # Данные схваток
    for fight in bracket.fights:
        fight_data = {
            'id': fight.id,
            'round': fight.round_number,
            'fight_number': fight.fight_number,
            'status': fight.status,
            'white_athlete': None,
            'blue_athlete': None,
            'winner': None
        }

        if fight.white_athlete:
            fight_data['white_athlete'] = {
                'id': fight.white_athlete.id,
                'name': fight.white_athlete.full_name
            }

        if fight.blue_athlete:
            fight_data['blue_athlete'] = {
                'id': fight.blue_athlete.id,
                'name': fight.blue_athlete.full_name
            }

        if fight.result:
            fight_data['winner'] = {
                'id': fight.result.winner_id,
                'name': fight.result.winner.full_name
            }

        bracket_data['fights'].append(fight_data)

    return jsonify(bracket_data)

@brackets_bp.route('/<int:tournament_id>/standings/<int:category_id>')
@admin_required
def bracket_standings(tournament_id, category_id):
    """Текущее положение в сетке"""
    tournament = Tournament.query.get_or_404(tournament_id)
    category = Category.query.get_or_404(category_id)
    bracket = category.get_bracket()

    if not bracket:
        flash('Сетка не найдена', 'danger')
        return redirect(url_for('brackets.list_brackets', tournament_id=tournament_id))

    standings = bracket.get_standings()

    return render_template(
        'admin/brackets/standings.html',
        tournament=tournament,
        category=category,
        bracket=bracket,
        standings=standings
    )