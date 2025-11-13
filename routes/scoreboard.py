"""
Маршруты для табло и публичного отображения
"""

from flask import Blueprint, render_template, request, jsonify
from models.tournament import Tournament
from models.fight import Fight
from services.fight_manager import FightManager
from services.timer_service import TimerService

scoreboard_bp = Blueprint('scoreboard', __name__)

@scoreboard_bp.route('/')
def main():
    """Главное табло"""
    # Активные турниры
    active_tournaments = Tournament.query.filter_by(status='LIVE').all()

    # Все активные схватки
    live_fights = FightManager.get_live_fights()

    # Группируем по татами
    fights_by_tatami = {}
    for fight in live_fights:
        if fight.tatami not in fights_by_tatami:
            fights_by_tatami[fight.tatami] = []
        fights_by_tatami[fight.tatami].append(fight)

    return render_template(
        'scoreboard/main.html',
        active_tournaments=active_tournaments,
        fights_by_tatami=fights_by_tatami
    )

@scoreboard_bp.route('/tatami/<int:tatami>')
def tatami(tatami):
    """Табло конкретного татами"""
    # Активные схватки на татами
    live_fights = FightManager.get_live_fights(tatami=tatami)

    # Следующие схватки
    scheduled_fights = FightManager.get_scheduled_fights(tatami=tatami)

    return render_template(
        'scoreboard/tatami.html',
        tatami=tatami,
        live_fights=live_fights,
        scheduled_fights=scheduled_fights
    )

@scoreboard_bp.route('/tournament/<int:tournament_id>')
def tournament(tournament_id):
    """Табло турнира"""
    tournament = Tournament.query.get_or_404(tournament_id)

    # Активные схватки турнира
    live_fights = FightManager.get_live_fights(tournament_id=tournament_id)

    # Результаты по категориям
    from services.result_calculator import ResultCalculator
    calculator = ResultCalculator(tournament_id)

    category_results = []
    for category in tournament.categories:
        results = calculator.calculate_category_results(category.id)
        if results:
            category_results.append(results)

    return render_template(
        'scoreboard/tournament.html',
        tournament=tournament,
        live_fights=live_fights,
        category_results=category_results
    )

@scoreboard_bp.route('/brackets/<int:tournament_id>')
def brackets(tournament_id):
    """Турнирные сетки"""
    tournament = Tournament.query.get_or_404(tournament_id)

    return render_template(
        'scoreboard/brackets.html',
        tournament=tournament
    )

@scoreboard_bp.route('/brackets/<int:tournament_id>/category/<int:category_id>')
def category_bracket(tournament_id, category_id):
    """Сетка конкретной категории"""
    tournament = Tournament.query.get_or_404(tournament_id)
    from models.category import Category
    category = Category.query.get_or_404(category_id)
    bracket = category.get_bracket()

    if not bracket:
        return "Сетка не найдена", 404

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
        'scoreboard/category_bracket.html',
        tournament=tournament,
        category=category,
        bracket=bracket,
        fights_by_round=fights_by_round,
        rounds=rounds
    )

@scoreboard_bp.route('/results/<int:tournament_id>')
def results(tournament_id):
    """Результаты турнира"""
    tournament = Tournament.query.get_or_404(tournament_id)

    from services.result_calculator import ResultCalculator
    calculator = ResultCalculator(tournament_id)

    # Результаты по категориям
    category_results = []
    for category in tournament.categories:
        results = calculator.calculate_category_results(category.id)
        if results:
            category_results.append(results)

    # Командный зачет
    team_ranking = calculator.calculate_team_ranking()

    # Общая статистика
    statistics = calculator.calculate_tournament_statistics()

    return render_template(
        'scoreboard/results.html',
        tournament=tournament,
        category_results=category_results,
        team_ranking=team_ranking,
        statistics=statistics
    )

@scoreboard_bp.route('/live')
def live():
    """Live результаты"""
    # Все активные турниры
    active_tournaments = Tournament.query.filter_by(status='LIVE').all()

    # Последние завершенные схватки
    from datetime import datetime, timedelta
    recent_fights = Fight.query.filter(
        Fight.status == 'COMPLETED',
        Fight.end_time >= datetime.utcnow() - timedelta(hours=24)
    ).order_by(Fight.end_time.desc()).limit(20).all()

    return render_template(
        'scoreboard/live.html',
        active_tournaments=active_tournaments,
        recent_fights=recent_fights
    )

@scoreboard_bp.route('/api/live_fights')
def api_live_fights():
    """API активных схваток"""
    tournament_id = request.args.get('tournament_id', type=int)
    tatami = request.args.get('tatami', type=int)

    live_fights = FightManager.get_live_fights(
        tournament_id=tournament_id,
        tatami=tatami
    )

    fights_data = []
    for fight in live_fights:
        fight_data = {
            'id': fight.id,
            'tatami': fight.tatami,
            'fight_number': fight.fight_number,
            'white_athlete': {
                'name': fight.white_athlete.full_name if fight.white_athlete else 'TBD',
                'club': fight.white_athlete.club.name if fight.white_athlete and fight.white_athlete.club else ''
            } if fight.white_athlete else None,
            'blue_athlete': {
                'name': fight.blue_athlete.full_name if fight.blue_athlete else 'TBD',
                'club': fight.blue_athlete.club.name if fight.blue_athlete and fight.blue_athlete.club else ''
            } if fight.blue_athlete else None,
            'category': fight.category.name if fight.category else '',
            'tournament': fight.tournament.name,
            'timer_seconds': fight.timer_seconds,
            'is_golden_score': fight.is_golden_score,
            'scores': {
                'white': 0,
                'blue': 0
            },
            'penalties': {
                'white': 0,
                'blue': 0
            }
        }

        # Добавляем результаты если есть
        if fight.result:
            fight_data['scores']['white'] = fight.result.white_score
            fight_data['scores']['blue'] = fight.result.blue_score
            fight_data['penalties']['white'] = fight.result.get_penalty_count('WHITE')
            fight_data['penalties']['blue'] = fight.result.get_penalty_count('BLUE')

        fights_data.append(fight_data)

    return jsonify(fights_data)

@scoreboard_bp.route('/api/fight_status/<int:fight_id>')
def api_fight_status(fight_id):
    """API статуса конкретной схватки"""
    fight = Fight.query.get_or_404(fight_id)

    fight_manager = FightManager(fight_id)
    fight_status = fight_manager.get_fight_status()

    return jsonify(fight_status)

@scoreboard_bp.route('/api/timer_status/<int:fight_id>')
def api_timer_status(fight_id):
    """API статуса таймера"""
    fight = Fight.query.get_or_404(fight_id)

    timer_service = TimerService.get_instance()
    timer_status = timer_service.get_timer_status(fight_id)

    return jsonify(timer_status)

@scoreboard_bp.route('/api/tournament_stats/<int:tournament_id>')
def api_tournament_stats(tournament_id):
    """API статистики турнира"""
    tournament = Tournament.query.get_or_404(tournament_id)

    from services.result_calculator import ResultCalculator
    calculator = ResultCalculator(tournament_id)
    statistics = calculator.calculate_tournament_statistics()

    return jsonify(statistics)

@scoreboard_bp.route('/api/recent_results')
def api_recent_results():
    """API последних результатов"""
    from datetime import datetime, timedelta

    recent_fights = Fight.query.filter(
        Fight.status == 'COMPLETED',
        Fight.end_time >= datetime.utcnow() - timedelta(hours=24)
    ).order_by(Fight.end_time.desc()).limit(10).all()

    results_data = []
    for fight in recent_fights:
        if fight.result and fight.result.winner:
            results_data.append({
                'tournament': fight.tournament.name,
                'category': fight.category.name if fight.category else '',
                'winner': fight.result.winner.full_name,
                'winner_club': fight.result.winner.club.name if fight.result.winner.club else '',
                'victory_type': fight.result.victory_description,
                'fight_duration': fight.result.fight_duration,
                'end_time': fight.end_time.strftime('%H:%M')
            })

    return jsonify(results_data)