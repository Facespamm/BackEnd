"""
Маршруты для судейского интерфейса
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from utils.security import referee_required, get_current_user, check_tatami_access
from models.tournament import Tournament
from models.fight import Fight
from services.fight_manager import FightManager
from services.timer_service import TimerService

referee_bp = Blueprint('referee', __name__)

@referee_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Вход для судей"""
    # Если судья уже авторизован, перенаправляем на dashboard
    if 'user_id' in session and session.get('user_role') == 'REFEREE':
        return redirect(url_for('referee.dashboard'))

    from utils.forms import RefereeLoginForm
    form = RefereeLoginForm()

    if form.validate_on_submit():
        tatami = form.tatami.data
        code = form.code.data.upper()

        # Простая проверка кода доступа (в реальной системе можно усложнить)
        expected_code = f"REF{tatami:02d}"

        if code == expected_code:
            # Находим пользователя-судью для этого татами
            from models.user import User
            referee = User.query.filter_by(
                role='REFEREE',
                tatami_assigned=tatami,
                is_active=True
            ).first()

            if referee:
                # Вход в систему
                session['user_id'] = referee.id
                session['user_username'] = referee.username
                session['user_name'] = referee.name
                session['user_role'] = referee.role
                session['user_tatami'] = referee.tatami_assigned
                session.permanent = True

                flash(f'Добро пожаловать, судья {referee.name}! Татами #{tatami}', 'success')
                return redirect(url_for('referee.dashboard'))
            else:
                flash('Судья не назначен на этот татами', 'danger')
        else:
            flash('Неверный код доступа', 'danger')

    return render_template('referee/login.html', form=form)

@referee_bp.route('/dashboard')
@referee_required
def dashboard():
    """Панель судьи"""
    user = get_current_user()
    tatami = user.tatami_assigned

    # Активные турниры
    active_tournaments = Tournament.query.filter_by(status='LIVE').all()

    # Схватки на татами судьи
    scheduled_fights = FightManager.get_scheduled_fights(tatami=tatami)
    live_fights = FightManager.get_live_fights(tatami=tatami)

    return render_template(
        'referee/dashboard.html',
        user=user,
        tatami=tatami,
        active_tournaments=active_tournaments,
        scheduled_fights=scheduled_fights,
        live_fights=live_fights
    )

@referee_bp.route('/fight/<int:fight_id>')
@referee_required
def fight_control(fight_id):
    """Управление схваткой (судейская версия)"""
    fight = Fight.query.get_or_404(fight_id)
    user = get_current_user()

    # Проверка доступа к татами
    if not check_tatami_access(fight.tatami):
        flash('Нет доступа к этому татами', 'danger')
        return redirect(url_for('referee.dashboard'))

    fight_manager = FightManager(fight_id)
    fight_status = fight_manager.get_fight_status()

    return render_template(
        'referee/fight_control.html',
        fight=fight,
        fight_status=fight_status,
        user=user
    )

@referee_bp.route('/fight/<int:fight_id>/start')
@referee_required
def start_fight(fight_id):
    """Начало схватки"""
    fight = Fight.query.get_or_404(fight_id)

    if not check_tatami_access(fight.tatami):
        return jsonify({'success': False, 'error': 'Нет доступа к этому татами'})

    fight_manager = FightManager(fight_id)

    if fight_manager.start_fight():
        # Запускаем таймер
        timer_service = TimerService.get_instance()
        timer_service.start_timer(fight_id)

        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Не удалось начать схватку'})

@referee_bp.route('/fight/<int:fight_id>/pause')
@referee_required
def pause_fight(fight_id):
    """Приостановка схватки"""
    fight = Fight.query.get_or_404(fight_id)

    if not check_tatami_access(fight.tatami):
        return jsonify({'success': False, 'error': 'Нет доступа к этому татами'})

    fight_manager = FightManager(fight_id)

    if fight_manager.pause_fight():
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Не удалось приостановить схватку'})

@referee_bp.route('/fight/<int:fight_id>/resume')
@referee_required
def resume_fight(fight_id):
    """Возобновление схватки"""
    fight = Fight.query.get_or_404(fight_id)

    if not check_tatami_access(fight.tatami):
        return jsonify({'success': False, 'error': 'Нет доступа к этому татами'})

    fight_manager = FightManager(fight_id)

    if fight_manager.resume_fight():
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Не удалось возобновить схватку'})

@referee_bp.route('/fight/<int:fight_id>/add_score', methods=['POST'])
@referee_required
def add_score(fight_id):
    """Добавление оценки"""
    fight = Fight.query.get_or_404(fight_id)

    if not check_tatami_access(fight.tatami):
        return jsonify({'success': False, 'error': 'Нет доступа к этому татами'})

    athlete_color = request.form.get('athlete_color')
    score_type = request.form.get('score_type')

    if not athlete_color or not score_type:
        return jsonify({'success': False, 'error': 'Не указаны параметры'})

    fight_manager = FightManager(fight_id)

    if fight_manager.add_score(athlete_color, score_type):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Не удалось добавить оценку'})

@referee_bp.route('/fight/<int:fight_id>/complete', methods=['POST'])
@referee_required
def complete_fight(fight_id):
    """Завершение схватки"""
    fight = Fight.query.get_or_404(fight_id)

    if not check_tatami_access(fight.tatami):
        return jsonify({'success': False, 'error': 'Нет доступа к этому татами'})

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

@referee_bp.route('/fight/<int:fight_id>/timer')
@referee_required
def fight_timer(fight_id):
    """Отдельная страница таймера"""
    fight = Fight.query.get_or_404(fight_id)

    if not check_tatami_access(fight.tatami):
        flash('Нет доступа к этому татами', 'danger')
        return redirect(url_for('referee.dashboard'))

    return render_template('referee/timer.html', fight=fight)

@referee_bp.route('/api/fight_status/<int:fight_id>')
@referee_required
def api_fight_status(fight_id):
    """API статуса схватки"""
    fight = Fight.query.get_or_404(fight_id)

    if not check_tatami_access(fight.tatami):
        return jsonify({'error': 'Нет доступа к этому татами'})

    fight_manager = FightManager(fight_id)
    fight_status = fight_manager.get_fight_status()

    return jsonify(fight_status)

@referee_bp.route('/api/timer_status/<int:fight_id>')
@referee_required
def api_timer_status(fight_id):
    """API статуса таймера"""
    fight = Fight.query.get_or_404(fight_id)

    if not check_tatami_access(fight.tatami):
        return jsonify({'error': 'Нет доступа к этому татами'})

    timer_service = TimerService.get_instance()
    timer_status = timer_service.get_timer_status(fight_id)

    return jsonify(timer_status)

@referee_bp.route('/api/update_timer/<int:fight_id>', methods=['POST'])
@referee_required
def api_update_timer(fight_id):
    """API обновления таймера"""
    fight = Fight.query.get_or_404(fight_id)

    if not check_tatami_access(fight.tatami):
        return jsonify({'success': False, 'error': 'Нет доступа к этому татами'})

    seconds = request.json.get('seconds')

    if seconds is None:
        return jsonify({'success': False, 'error': 'Не указано время'})

    timer_service = TimerService.get_instance()

    if timer_service.set_timer(fight_id, seconds):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Не удалось обновить таймер'})

@referee_bp.route('/api/active_fights')
@referee_required
def api_active_fights():
    """API активных схваток на татами"""
    user = get_current_user()
    tatami = user.tatami_assigned

    live_fights = FightManager.get_live_fights(tatami=tatami)
    scheduled_fights = FightManager.get_scheduled_fights(tatami=tatami)

    fights_data = {
        'live': [],
        'scheduled': []
    }

    for fight in live_fights:
        fights_data['live'].append({
            'id': fight.id,
            'fight_number': fight.fight_number,
            'white_athlete': fight.white_athlete.full_name if fight.white_athlete else 'TBD',
            'blue_athlete': fight.blue_athlete.full_name if fight.blue_athlete else 'TBD',
            'category': fight.category.name if fight.category else '',
            'tournament': fight.tournament.name
        })

    for fight in scheduled_fights:
        fights_data['scheduled'].append({
            'id': fight.id,
            'fight_number': fight.fight_number,
            'white_athlete': fight.white_athlete.full_name if fight.white_athlete else 'TBD',
            'blue_athlete': fight.blue_athlete.full_name if fight.blue_athlete else 'TBD',
            'category': fight.category.name if fight.category else '',
            'tournament': fight.tournament.name,
            'scheduled_time': fight.scheduled_time.strftime('%H:%M') if fight.scheduled_time else ''
        })

    return jsonify(fights_data)

@referee_bp.route('/quick_actions')
@referee_required
def quick_actions():
    """Быстрые действия для судьи"""
    user = get_current_user()
    tatami = user.tatami_assigned

    # Следующие схватки
    next_fights = Fight.query.filter_by(
        tatami=tatami,
        status='SCHEDULED'
    ).order_by(Fight.scheduled_time).limit(3).all()

    return render_template(
        'referee/quick_actions.html',
        user=user,
        tatami=tatami,
        next_fights=next_fights
    )