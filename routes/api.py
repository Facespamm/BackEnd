"""
API маршруты для внешних систем и мобильных приложений
"""

from flask import Blueprint, request, jsonify
from models.tournament import Tournament
from models.fight import Fight
from models.athlete import Athlete
from models.club import Club
from services.fight_manager import FightManager
from services.timer_service import TimerService
from database.db import db

api_bp = Blueprint('api', __name__)

# Простой API ключ для демонстрации (в реальной системе использовать JWT)
API_KEYS = {
    'mobile_app_2024': 'mobile_client',
    'scoreboard_2024': 'scoreboard_client'
}

def require_api_key(f):
    """Декоратор для проверки API ключа"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')

        if not api_key or api_key not in API_KEYS:
            return jsonify({'error': 'Invalid API key'}), 401

        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/tournaments')
@require_api_key
def api_tournaments():
    """API списка турниров"""
    status = request.args.get('status', '')
    limit = request.args.get('limit', 50, type=int)

    query = Tournament.query

    if status:
        query = query.filter_by(status=status)

    tournaments = query.order_by(Tournament.start_date.desc()).limit(limit).all()

    tournaments_data = []
    for tournament in tournaments:
        tournaments_data.append({
            'id': tournament.id,
            'name': tournament.name,
            'description': tournament.description,
            'start_date': tournament.start_date.isoformat(),
            'end_date': tournament.end_date.isoformat(),
            'venue': tournament.venue,
            'city': tournament.city,
            'country': tournament.country,
            'status': tournament.status,
            'tatami_count': tournament.tatami_count,
            'athletes_count': tournament.athletes_count,
            'progress_percentage': tournament.progress_percentage
        })

    return jsonify({
        'tournaments': tournaments_data,
        'total': len(tournaments_data)
    })

@api_bp.route('/tournaments/<int:tournament_id>')
@require_api_key
def api_tournament_detail(tournament_id):
    """API детальной информации о турнире"""
    tournament = Tournament.query.get_or_404(tournament_id)

    # Категории турнира
    categories_data = []
    for category in tournament.categories:
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'gender': category.gender,
            'weight_range': category.weight_range,
            'age_range': category.age_range,
            'athletes_count': category.athletes_count
        })

    tournament_data = {
        'id': tournament.id,
        'name': tournament.name,
        'description': tournament.description,
        'start_date': tournament.start_date.isoformat(),
        'end_date': tournament.end_date.isoformat(),
        'venue': tournament.venue,
        'address': tournament.address,
        'city': tournament.city,
        'country': tournament.country,
        'status': tournament.status,
        'tatami_count': tournament.tatami_count,
        'fight_duration': tournament.fight_duration,
        'golden_score_duration': tournament.golden_score_duration,
        'organizer': tournament.organizer,
        'chief_referee': tournament.chief_referee,
        'categories': categories_data,
        'statistics': {
            'total_athletes': tournament.athletes_count,
            'total_fights': tournament.total_fights_count,
            'completed_fights': tournament.completed_fights_count,
            'progress_percentage': tournament.progress_percentage
        }
    }

    return jsonify(tournament_data)

@api_bp.route('/tournaments/<int:tournament_id>/fights')
@require_api_key
def api_tournament_fights(tournament_id):
    """API схваток турнира"""
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

    fights = query.order_by(Fight.tatami, Fight.scheduled_time).all()

    fights_data = []
    for fight in fights:
        fight_data = {
            'id': fight.id,
            'tatami': fight.tatami,
            'fight_number': fight.fight_number,
            'round_number': fight.round_number,
            'status': fight.status,
            'scheduled_time': fight.scheduled_time.isoformat() if fight.scheduled_time else None,
            'start_time': fight.start_time.isoformat() if fight.start_time else None,
            'end_time': fight.end_time.isoformat() if fight.end_time else None,
            'timer_seconds': fight.timer_seconds,
            'is_golden_score': fight.is_golden_score,
            'white_athlete': None,
            'blue_athlete': None,
            'category': None,
            'result': None
        }

        if fight.white_athlete:
            fight_data['white_athlete'] = {
                'id': fight.white_athlete.id,
                'name': fight.white_athlete.full_name,
                'club': fight.white_athlete.club.name if fight.white_athlete.club else ''
            }

        if fight.blue_athlete:
            fight_data['blue_athlete'] = {
                'id': fight.blue_athlete.id,
                'name': fight.blue_athlete.full_name,
                'club': fight.blue_athlete.club.name if fight.blue_athlete.club else ''
            }

        if fight.category:
            fight_data['category'] = {
                'id': fight.category.id,
                'name': fight.category.name
            }

        if fight.result:
            fight_data['result'] = {
                'winner_id': fight.result.winner_id,
                'victory_type': fight.result.victory_type,
                'details': fight.result.details,
                'white_score': fight.result.white_score,
                'blue_score': fight.result.blue_score,
                'fight_duration': fight.result.fight_duration
            }

        fights_data.append(fight_data)

    return jsonify({
        'fights': fights_data,
        'total': len(fights_data)
    })

@api_bp.route('/fights/<int:fight_id>')
@require_api_key
def api_fight_detail(fight_id):
    """API детальной информации о схватке"""
    fight = Fight.query.get_or_404(fight_id)

    fight_manager = FightManager(fight_id)
    fight_status = fight_manager.get_fight_status()

    return jsonify(fight_status)

@api_bp.route('/fights/<int:fight_id>/timer')
@require_api_key
def api_fight_timer(fight_id):
    """API статуса таймера схватки"""
    fight = Fight.query.get_or_404(fight_id)

    timer_service = TimerService.get_instance()
    timer_status = timer_service.get_timer_status(fight_id)

    return jsonify(timer_status)

@api_bp.route('/live/fights')
@require_api_key
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
            'tournament': fight.tournament.name,
            'category': fight.category.name if fight.category else '',
            'white_athlete': fight.white_athlete.full_name if fight.white_athlete else 'TBD',
            'blue_athlete': fight.blue_athlete.full_name if fight.blue_athlete else 'TBD',
            'timer_seconds': fight.timer_seconds,
            'is_golden_score': fight.is_golden_score,
            'scores': {'white': 0, 'blue': 0},
            'penalties': {'white': 0, 'blue': 0}
        }

        if fight.result:
            fight_data['scores']['white'] = fight.result.white_score
            fight_data['scores']['blue'] = fight.result.blue_score
            fight_data['penalties']['white'] = fight.result.get_penalty_count('WHITE')
            fight_data['penalties']['blue'] = fight.result.get_penalty_count('BLUE')

        fights_data.append(fight_data)

    return jsonify({'live_fights': fights_data})

@api_bp.route('/athletes')
@require_api_key
def api_athletes():
    """API списка участников"""
    search = request.args.get('search', '')
    club_id = request.args.get('club_id', type=int)
    limit = request.args.get('limit', 100, type=int)

    query = Athlete.query.filter_by(is_active=True)

    if search:
        query = query.filter(
            db.or_(
                Athlete.last_name.ilike(f'%{search}%'),
                Athlete.first_name.ilike(f'%{search}%')
            )
        )

    if club_id:
        query = query.filter_by(club_id=club_id)

    athletes = query.order_by(Athlete.last_name, Athlete.first_name).limit(limit).all()

    athletes_data = []
    for athlete in athletes:
        athletes_data.append({
            'id': athlete.id,
            'first_name': athlete.first_name,
            'last_name': athlete.last_name,
            'middle_name': athlete.middle_name,
            'full_name': athlete.full_name,
            'birth_date': athlete.birth_date.isoformat(),
            'age': athlete.age,
            'gender': athlete.gender,
            'club': athlete.club.name if athlete.club else '',
            'rank': athlete.rank,
            'license_number': athlete.license_number
        })

    return jsonify({
        'athletes': athletes_data,
        'total': len(athletes_data)
    })

@api_bp.route('/clubs')
@require_api_key
def api_clubs():
    """API списка клубов"""
    search = request.args.get('search', '')
    city = request.args.get('city', '')
    limit = request.args.get('limit', 50, type=int)

    query = Club.query.filter_by(is_active=True)

    if search:
        query = query.filter(Club.name.ilike(f'%{search}%'))

    if city:
        query = query.filter(Club.city.ilike(f'%{city}%'))

    clubs = query.order_by(Club.name).limit(limit).all()

    clubs_data = []
    for club in clubs:
        clubs_data.append({
            'id': club.id,
            'name': club.name,
            'short_name': club.short_name,
            'city': club.city,
            'country': club.country,
            'coach_name': club.coach_name,
            'athletes_count': club.athletes_count
        })

    return jsonify({
        'clubs': clubs_data,
        'total': len(clubs_data)
    })

@api_bp.route('/results/tournament/<int:tournament_id>')
@require_api_key
def api_tournament_results(tournament_id):
    """API результатов турнира"""
    tournament = Tournament.query.get_or_404(tournament_id)

    from services.result_calculator import ResultCalculator
    calculator = ResultCalculator(tournament_id)

    # Результаты по категориям
    categories_results = []
    for category in tournament.categories:
        results = calculator.calculate_category_results(category.id)
        if results:
            categories_results.append(results)

    # Командный зачет
    team_ranking = calculator.calculate_team_ranking()

    # Общая статистика
    statistics = calculator.calculate_tournament_statistics()

    return jsonify({
        'tournament': {
            'id': tournament.id,
            'name': tournament.name,
            'status': tournament.status
        },
        'categories_results': categories_results,
        'team_ranking': team_ranking,
        'statistics': statistics
    })

@api_bp.route('/rankings/athletes')
@require_api_key
def api_athlete_rankings():
    """API рейтинга участников"""
    limit = request.args.get('limit', 100, type=int)

    from services.ranking_service import RankingService
    ranking_service = RankingService()

    rankings = ranking_service.calculate_athlete_ranking(limit=limit)

    rankings_data = []
    for ranking in rankings:
        rankings_data.append({
            'position': ranking['position'],
            'athlete': {
                'id': ranking['athlete'].id,
                'name': ranking['athlete'].full_name,
                'club': ranking['athlete'].club.name if ranking['athlete'].club else ''
            },
            'ranking_points': ranking['ranking_points'],
            'stats': ranking['stats']
        })

    return jsonify({'rankings': rankings_data})

@api_bp.route('/rankings/clubs')
@require_api_key
def api_club_rankings():
    """API рейтинга клубов"""
    limit = request.args.get('limit', 50, type=int)

    from services.ranking_service import RankingService
    ranking_service = RankingService()

    rankings = ranking_service.calculate_club_ranking(limit=limit)

    rankings_data = []
    for ranking in rankings:
        rankings_data.append({
            'position': ranking['position'],
            'club': {
                'id': ranking['club'].id,
                'name': ranking['club'].name,
                'city': ranking['club'].city
            },
            'ranking_points': ranking['ranking_points'],
            'stats': ranking['stats']
        })

    return jsonify({'rankings': rankings_data})

@api_bp.route('/system/status')
@require_api_key
def api_system_status():
    """API статуса системы"""
    from datetime import datetime

    # Статистика системы
    stats = {
        'total_tournaments': Tournament.query.count(),
        'active_tournaments': Tournament.query.filter_by(status='LIVE').count(),
        'total_athletes': Athlete.query.filter_by(is_active=True).count(),
        'total_clubs': Club.query.filter_by(is_active=True).count(),
        'live_fights': Fight.query.filter_by(status='LIVE').count(),
        'server_time': datetime.utcnow().isoformat()
    }

    return jsonify({
        'status': 'online',
        'version': '1.0.0',
        'stats': stats
    })

@api_bp.route('/webhook/fight_update', methods=['POST'])
@require_api_key
def webhook_fight_update():
    """Webhook для обновления статуса схватки"""
    data = request.json

    if not data or 'fight_id' not in data:
        return jsonify({'error': 'Missing fight_id'}), 400

    fight_id = data['fight_id']
    fight = Fight.query.get(fight_id)

    if not fight:
        return jsonify({'error': 'Fight not found'}), 404

    # Обновляем статус если предоставлен
    if 'status' in data:
        fight.status = data['status']

    # Обновляем таймер если предоставлен
    if 'timer_seconds' in data:
        fight.timer_seconds = data['timer_seconds']

    # Обновляем золотой скор если предоставлен
    if 'is_golden_score' in data:
        fight.is_golden_score = data['is_golden_score']

    fight.save()

    return jsonify({'success': True, 'message': 'Fight updated'})