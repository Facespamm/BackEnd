"""
Публичные маршруты (доступны без авторизации)
"""

from flask import Blueprint, render_template, request, jsonify
from models.tournament import Tournament
from models.athlete import Athlete
from models.club import Club


public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    """Главная публичная страница"""
    # Активные турниры
    # active_tournaments = Tournament.query.filter_by(status='LIVE').order_by(
    #     Tournament.start_date.desc()
    # ).limit(3).all()

    # # Ближайшие турниры
    # upcoming_tournaments = Tournament.query.filter(
    #     Tournament.status.in_(['PLANNED', 'REGISTRATION'])
    # ).order_by(Tournament.start_date).limit(3).all()

    # # Последние завершенные турниры
    # completed_tournaments = Tournament.query.filter_by(status='COMPLETED').order_by(
    #     Tournament.end_date.desc()
    # ).limit(3).all()

    return render_template(
        'public/index.html',
        # active_tournaments=active_tournaments,
        # upcoming_tournaments=upcoming_tournaments,
        # completed_tournaments=completed_tournaments
    )

@public_bp.route('/tournaments')
def tournaments():
    """Список всех турниров"""
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')

    query = Tournament.query

    if status_filter:
        query = query.filter_by(status=status_filter)

    if search:
        query = query.filter(Tournament.name.ilike(f'%{search}%'))

    tournaments_list = query.order_by(Tournament.start_date.desc()).all()

    return render_template(
        'public/tournaments.html',
        tournaments=tournaments_list,
        status_filter=status_filter,
        search=search
    )

@public_bp.route('/tournament/<int:tournament_id>')
def tournament_detail(tournament_id):
    """Детальная информация о турнире"""
    tournament = Tournament.query.get_or_404(tournament_id)

    return render_template(
        'public/tournament_detail.html',
        tournament=tournament
    )

@public_bp.route('/athletes')
def athletes():
    """Список участников"""
    search = request.args.get('search', '')
    club_id = request.args.get('club_id', type=int)

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

    athletes_list = query.order_by(Athlete.last_name, Athlete.first_name).all()
    clubs = Club.query.filter_by(is_active=True).order_by(Club.name).all()

    return render_template(
        'public/athletes.html',
        athletes=athletes_list,
        clubs=clubs,
        search=search,
        club_id=club_id
    )

@public_bp.route('/athlete/<int:athlete_id>')
def athlete_profile(athlete_id):
    """Профиль участника"""
    athlete = Athlete.query.get_or_404(athlete_id)

    if not athlete.is_active:
        return "Участник не найден", 404

    # Статистика участника
    from services.ranking_service import RankingService
    ranking_service = RankingService()
    stats = ranking_service._get_athlete_stats(athlete)

    # История выступлений
    from models.fight import Fight
    fights = Fight.query.filter(
        ((Fight.white_athlete_id == athlete_id) | (Fight.blue_athlete_id == athlete_id)) &
        (Fight.status == 'COMPLETED')
    ).order_by(Fight.created_at.desc()).limit(10).all()

    return render_template(
        'public/athlete_profile.html',
        athlete=athlete,
        stats=stats,
        fights=fights
    )

@public_bp.route('/clubs')
def clubs():
    """Список клубов"""
    search = request.args.get('search', '')
    city = request.args.get('city', '')

    query = Club.query.filter_by(is_active=True)

    if search:
        query = query.filter(Club.name.ilike(f'%{search}%'))

    if city:
        query = query.filter(Club.city.ilike(f'%{city}%'))

    clubs_list = query.order_by(Club.name).all()

    # Собираем уникальные города для фильтра
    cities = db.session.query(Club.city).filter(
        Club.city.isnot(None),
        Club.city != ''
    ).distinct().order_by(Club.city).all()
    cities = [city[0] for city in cities]

    return render_template(
        'public/clubs.html',
        clubs=clubs_list,
        cities=cities,
        search=search,
        city_filter=city
    )

@public_bp.route('/club/<int:club_id>')
def club_detail(club_id):
    """Детальная информация о клубе"""
    club = Club.query.get_or_404(club_id)

    if not club.is_active:
        return "Клуб не найден", 404

    # Участники клуба
    athletes = club.athletes

    # Статистика клуба
    from services.ranking_service import RankingService
    ranking_service = RankingService()
    stats = ranking_service._get_club_stats(club)

    return render_template(
        'public/club_detail.html',
        club=club,
        athletes=athletes,
        stats=stats
    )

@public_bp.route('/rankings')
def rankings():
    """Рейтинги участников и клубов"""
    ranking_type = request.args.get('type', 'athletes')

    from services.ranking_service import RankingService
    ranking_service = RankingService()

    if ranking_type == 'athletes':
        athlete_rankings = ranking_service.calculate_athlete_ranking(limit=100)
        return render_template(
            'public/athlete_rankings.html',
            rankings=athlete_rankings,
            ranking_type='athletes'
        )
    else:
        club_rankings = ranking_service.calculate_club_ranking(limit=50)
        return render_template(
            'public/club_rankings.html',
            rankings=club_rankings,
            ranking_type='clubs'
        )

@public_bp.route('/schedule')
def schedule():
    """Расписание турниров"""
    # Турниры на этой неделе
    from datetime import datetime, timedelta
    start_of_week = datetime.now().date() - timedelta(days=datetime.now().weekday())
    end_of_week = start_of_week + timedelta(days=6)

    week_tournaments = Tournament.query.filter(
        Tournament.start_date <= end_of_week,
        Tournament.end_date >= start_of_week
    ).order_by(Tournament.start_date).all()

    # Турниры по месяцам
    from sqlalchemy import extract
    current_year = datetime.now().year

    monthly_tournaments = {}
    for month in range(1, 13):
        month_tournaments = Tournament.query.filter(
            extract('year', Tournament.start_date) == current_year,
            extract('month', Tournament.start_date) == month
        ).order_by(Tournament.start_date).all()

        if month_tournaments:
            monthly_tournaments[month] = month_tournaments

    return render_template(
        'public/schedule.html',
        week_tournaments=week_tournaments,
        monthly_tournaments=monthly_tournaments,
        current_year=current_year
    )

@public_bp.route('/results')
def results():
    """Результаты турниров"""
    # Завершенные турниры
    completed_tournaments = Tournament.query.filter_by(status='COMPLETED').order_by(
        Tournament.end_date.desc()
    ).all()

    return render_template(
        'public/results.html',
        tournaments=completed_tournaments
    )

@public_bp.route('/api/search')
def api_search():
    """API поиска"""
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')

    if len(query) < 2:
        return jsonify([])

    results = []

    if search_type in ['all', 'athletes']:
        athletes = Athlete.query.filter(
            db.or_(
                Athlete.last_name.ilike(f'%{query}%'),
                Athlete.first_name.ilike(f'%{query}%')
            )
        ).filter_by(is_active=True).limit(5).all()

        for athlete in athletes:
            results.append({
                'type': 'athlete',
                'id': athlete.id,
                'name': athlete.full_name,
                'club': athlete.club.name if athlete.club else '',
                'url': url_for('public.athlete_profile', athlete_id=athlete.id)
            })

    if search_type in ['all', 'clubs']:
        clubs = Club.query.filter(
            Club.name.ilike(f'%{query}%')
        ).filter_by(is_active=True).limit(5).all()

        for club in clubs:
            results.append({
                'type': 'club',
                'id': club.id,
                'name': club.name,
                'city': club.city or '',
                'url': url_for('public.club_detail', club_id=club.id)
            })

    if search_type in ['all', 'tournaments']:
        tournaments = Tournament.query.filter(
            Tournament.name.ilike(f'%{query}%')
        ).limit(5).all()

        for tournament in tournaments:
            results.append({
                'type': 'tournament',
                'id': tournament.id,
                'name': tournament.name,
                'dates': f"{tournament.start_date} - {tournament.end_date}",
                'url': url_for('public.tournament_detail', tournament_id=tournament.id)
            })

    return jsonify(results)

@public_bp.route('/about')
def about():
    """О системе"""
    return render_template('public/about.html')

@public_bp.route('/contact')
def contact():
    """Контакты"""
    return render_template('public/contact.html')