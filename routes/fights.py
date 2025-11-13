"""
Маршруты для управления схватками
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from utils.security import admin_required
from models.tournament import Tournament
from models.fight import Fight
from services.fight_manager import FightManager
from services.timer_service import TimerService

fights_bp = Blueprint('fights', __name__)

@fights_bp.route('/<int:tournament_id>')
@admin_required
def list_fights(tournament_id):
    """Список схваток турнира"""
    tournament = Tournament.query.get_or_404(tournament_id)

    # Фильтры
    status = request.args.get('status', '')
    tatami = request.args.get('tatami', type=int)
    category_id = request.args.get('category_id', type=int)

    query = Fight.query.filter_by(tournament_id=tournament_id)

    if status:
        query = query.filter_by(status=status)

    if tatami:
        query = query.filter_by(tatami=tatami)

    if category_id:
        query = query.filter_by(category_id=category_id)

    fights = query.order_by(
        Fight.tatami, 
        Fight.scheduled_time, 
        Fight.round_number.desc()
    ).all()

    return render_template(
        'admin/fights/list.html',
        tournament=tournament,
        fights=fights,
        status_filter=status,
        tatami_filter=tatami,
        category_id_filter=category_id
    )

@fights_bp.route('/<int:tournament_id>/live')
@admin_required
def live_fights(tournament_id):
    """Активные схватки"""
    tournament = Tournament.query.get_or_404(tournament_id)

    live_fights = FightManager.get_live_fights(tournament_id)

    return render_template(
        'admin/fights/live.html',
        tournament=tournament,
        live_fights=live_fights
    )

@fights_bp.route('/<int:tournament_id>/control/<int:fight_id>')
@admin_required
def fight_control(tournament_id, fight_id):
    """Управление схваткой (админская версия)"""
    tournament = Tournament.query.get_or_404(tournament_id)
    fight = Fight.query.get_or_404(fight_id)

    if fight.tournament_id != tournament_id:
        flash('Схватка не принадлежит этому турниру', 'danger')
        return redirect(url_for('fights.list_fights', tournament_id=tournament_id))

    fight_manager = FightManager(fight_id)
    fight_status = fight_manager.get_fight_status()

    return render_template(
        'admin/fights/control.html',
        tournament=tournament,
        fight=fight,
        fight_status=fight_status
    )

@fights_bp.route('/<int:tournament_id>/start/<int:fight_id>')
@admin_required
def start_fight(tournament_id, fight_id):
    """Начало схватки"""
    fight = Fight.query.get_or_404(fight_id)

    if fight.tournament_id != tournament_id:
        flash('Схватка не принадлежит этому турниру', 'danger')
        return redirect(url_for('fights.list_fights', tournament_id=tournament_id))

    fight_manager = FightManager(fight_id)

    if fight_manager.start_fight():
        # Запускаем таймер
        timer_service = TimerService.get_instance()
        timer_service.start_timer(fight_id)

        flash('Схватка начата', 'success')
    else:
        flash('Не удалось начать схватку', 'danger')

    return redirect(url_for('fights.fight_control', tournament_id=tournament_id, fight_id=fight_id))

@fights_bp.route('/<int:tournament_id>/pause/<int:fight_id>')
@admin_required
def pause_fight(tournament_id, fight_id):
    """Приостановка схватки"""
    fight = Fight.query.get_or_404(fight_id)

    if fight.tournament_id != tournament_id:
        return jsonify({'success': False, 'error': 'Схватка не принадлежит этому турниру'})

    fight_manager = FightManager(fight_id)

    if fight_manager.pause_fight():
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Не удалось приостановить схватку'})

@fights_bp.route('/<int:tournament_id>/resume/<int:fight_id>')
@admin_required
def resume_fight(tournament_id, fight_id):
    """Возобновление схватки"""
    fight = Fight.query.get_or_404(fight_id)

    if fight.tournament_id != tournament_id:
        return jsonify({'success': False, 'error': 'Схватка не принадлежит этому турниру'})

    fight_manager = FightManager(fight_id)

    if fight_manager.resume_fight():
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Не удалось возобновить схватку'})

@fights_bp.route('/<int:tournament_id>/add_score/<int:fight_id>', methods=['POST'])
@admin_required
def add_score(tournament_id, fight_id):
    """Добавление оценки"""
    fight = Fight.query.get_or_404(fight_id)

    if fight.tournament_id != tournament_id:
        return jsonify({'success': False, 'error': 'Схватка не принадлежит этому турниру'})

    athlete_color = request.form.get('athlete_color')
    score_type = request.form.get('score_type')

    if not athlete_color or not score_type:
        return jsonify({'success': False, 'error': 'Не указаны параметры'})

    fight_manager = FightManager(fight_id)

    if fight_manager.add_score(athlete_color, score_type):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Не удалось добавить оценку'})

@fights_bp.route('/<int:tournament_id>/complete/<int:fight_id>', methods=['POST'])
@admin_required
def complete_fight(tournament_id, fight_id):
    """Завершение схватки"""
    fight = Fight.query.get_or_404(fight_id)

    if fight.tournament_id != tournament_id:
        return jsonify({'success': False, 'error': 'Схватка не принадлежит этому турниру'})

    winner_id = request.form.get('winner_id')
    victory_type = request.form.get('victory_type')
    details = request.form.get('details', '')

    if not winner_id or not victory_type:
        return jsonify({'success': False, 'error': 'Не указаны победитель или тип победы'})

    fight_manager = FightManager(fight_id)

    if fight_manager.complete_fight(int(winner_id), victory_type, details):
        # Останавливаем таймер
        timer_service = TimerService.get_instance()
        timer_service.stop_timer(fight_id)

        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Не удалось завершить схватку'})

@fights_bp.route('/<int:tournament_id>/cancel/<int:fight_id>', methods=['POST'])
@admin_required
def cancel_fight(tournament_id, fight_id):
    """Отмена схватки"""
    fight = Fight.query.get_or_404(fight_id)

    if fight.tournament_id != tournament_id:
        flash('Схватка не принадлежит этому турниру', 'danger')
        return redirect(url_for('fights.list_fights', tournament_id=tournament_id))

    reason = request.form.get('reason', '')

    fight_manager = FightManager(fight_id)

    if fight_manager.cancel_fight(reason):
        flash('Схватка отменена', 'success')
    else:
        flash('Не удалось отменить схватку', 'danger')

    return redirect(url_for('fights.list_fights', tournament_id=tournament_id))

@fights_bp.route('/<int:tournament_id>/api/fight_status/<int:fight_id>')
@admin_required
def api_fight_status(tournament_id, fight_id):
    """API статуса схватки"""
    fight = Fight.query.get_or_404(fight_id)

    if fight.tournament_id != tournament_id:
        return jsonify({'error': 'Схватка не принадлежит этому турниру'})

    fight_manager = FightManager(fight_id)
    fight_status = fight_manager.get_fight_status()

    return jsonify(fight_status)

@fights_bp.route('/<int:tournament_id>/api/timer_status/<int:fight_id>')
@admin_required
def api_timer_status(tournament_id, fight_id):
    """API статуса таймера"""
    fight = Fight.query.get_or_404(fight_id)

    if fight.tournament_id != tournament_id:
        return jsonify({'error': 'Схватка не принадлежит этому турниру'})

    timer_service = TimerService.get_instance()
    timer_status = timer_service.get_timer_status(fight_id)

    return jsonify(timer_status)

@fights_bp.route('/<int:tournament_id>/api/update_timer/<int:fight_id>', methods=['POST'])
@admin_required
def api_update_timer(tournament_id, fight_id):
    """API обновления таймера"""
    fight = Fight.query.get_or_404(fight_id)

    if fight.tournament_id != tournament_id:
        return jsonify({'success': False, 'error': 'Схватка не принадлежит этому турниру'})

    seconds = request.json.get('seconds')

    if seconds is None:
        return jsonify({'success': False, 'error': 'Не указано время'})

    timer_service = TimerService.get_instance()

    if timer_service.set_timer(fight_id, seconds):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Не удалось обновить таймер'})

@fights_bp.route('/<int:tournament_id>/bulk_actions', methods=['POST'])
@admin_required
def bulk_actions(tournament_id):
    """Массовые действия со схватками"""
    action = request.form.get('action')
    fight_ids = request.form.getlist('fight_ids')

    if not action or not fight_ids:
        flash('Не выбрано действие или схватки', 'danger')
        return redirect(url_for('fights.list_fights', tournament_id=tournament_id))

    success_count = 0
    error_count = 0

    for fight_id in fight_ids:
        fight = Fight.query.get(fight_id)
        if not fight or fight.tournament_id != tournament_id:
            error_count += 1
            continue

        fight_manager = FightManager(fight_id)

        if action == 'start' and fight.status == 'SCHEDULED':
            if fight_manager.start_fight():
                success_count += 1
            else:
                error_count += 1
        elif action == 'cancel' and fight.status in ['SCHEDULED', 'LIVE']:
            if fight_manager.cancel_fight('Массовая отмена'):
                success_count += 1
            else:
                error_count += 1

    flash(f'Успешно выполнено: {success_count}, ошибок: {error_count}', 'info')
    return redirect(url_for('fights.list_fights', tournament_id=tournament_id))