"""
Сервис расчета рейтингов и статистики
"""

from models.athlete import Athlete
from models.club import Club
from models.tournament import Tournament
from models.result import Result
from models.fight import Fight
from utils.helpers import calculate_ranking_points

class RankingService:
    """Сервис расчета рейтингов"""

    def __init__(self):
        pass

    def calculate_athlete_ranking(self, athlete_id=None, limit=100):
        """Расчет рейтинга участников"""
        athletes = Athlete.query.filter_by(is_active=True)

        if athlete_id:
            athletes = athletes.filter_by(id=athlete_id)

        athlete_rankings = []

        for athlete in athletes.limit(limit).all():
            stats = self._get_athlete_stats(athlete)
            athlete_rankings.append({
                'athlete': athlete,
                'stats': stats,
                'ranking_points': stats['total_points']
            })

        # Сортируем по рейтинговым очкам
        athlete_rankings.sort(key=lambda x: x['ranking_points'], reverse=True)

        # Добавляем позиции
        for i, ranking in enumerate(athlete_rankings):
            ranking['position'] = i + 1

        return athlete_rankings

    def calculate_club_ranking(self, limit=50):
        """Расчет рейтинга клубов"""
        clubs = Club.query.filter_by(is_active=True).limit(limit).all()
        club_rankings = []

        for club in clubs:
            stats = self._get_club_stats(club)
            club_rankings.append({
                'club': club,
                'stats': stats,
                'ranking_points': stats['total_points']
            })

        # Сортируем по рейтинговым очкам
        club_rankings.sort(key=lambda x: x['ranking_points'], reverse=True)

        # Добавляем позиции
        for i, ranking in enumerate(club_rankings):
            ranking['position'] = i + 1

        return club_rankings

    def _get_athlete_stats(self, athlete):
        """Получить статистику участника"""
        fights = Fight.query.filter(
            ((Fight.white_athlete_id == athlete.id) | (Fight.blue_athlete_id == athlete.id)) &
            (Fight.status == 'COMPLETED')
        ).all()

        stats = {
            'total_fights': len(fights),
            'victories': 0,
            'defeats': 0,
            'ippon_victories': 0,
            'wazaari_victories': 0,
            'shido_victories': 0,
            'quick_victories': 0,
            'total_points': 0,
            'tournaments_count': 0,
            'gold_medals': 0,
            'silver_medals': 0,
            'bronze_medals': 0
        }

        # Уникальные турниры
        tournament_ids = set()

        for fight in fights:
            if fight.status == 'COMPLETED' and fight.result:
                tournament_ids.add(fight.tournament_id)

                if fight.result.winner_id == athlete.id:
                    stats['victories'] += 1
                    points = calculate_ranking_points(
                        fight.result.victory_type,
                        fight.result.fight_duration
                    )
                    stats['total_points'] += points

                    if fight.result.is_ippon:
                        stats['ippon_victories'] += 1
                    if fight.result.is_wazaari:
                        stats['wazaari_victories'] += 1
                    if fight.result.victory_type == 'SHIDO':
                        stats['shido_victories'] += 1
                    if fight.result.is_quick_victory:
                        stats['quick_victories'] += 1

                    # Определяем медали по раунду
                    if fight.round_number == 1:  # Финал
                        stats['gold_medals'] += 1
                    elif fight.round_number == 2:  # Полуфинал/за 3 место
                        stats['silver_medals'] += 1
                    elif fight.round_number == 3:  # Бронза
                        stats['bronze_medals'] += 1
                else:
                    stats['defeats'] += 1

        stats['tournaments_count'] = len(tournament_ids)
        stats['win_rate'] = (stats['victories'] / stats['total_fights'] * 100) if stats['total_fights'] > 0 else 0

        return stats

    def _get_club_stats(self, club):
        """Получить статистику клуба"""
        athletes = club.athletes
        stats = {
            'total_athletes': len(athletes),
            'active_athletes': len([a for a in athletes if a.is_active]),
            'total_fights': 0,
            'total_victories': 0,
            'total_points': 0,
            'gold_medals': 0,
            'silver_medals': 0,
            'bronze_medals': 0,
            'tournaments_count': 0
        }

        # Уникальные турниры
        tournament_ids = set()

        for athlete in athletes:
            athlete_stats = self._get_athlete_stats(athlete)

            stats['total_fights'] += athlete_stats['total_fights']
            stats['total_victories'] += athlete_stats['victories']
            stats['total_points'] += athlete_stats['total_points']
            stats['gold_medals'] += athlete_stats['gold_medals']
            stats['silver_medals'] += athlete_stats['silver_medals']
            stats['bronze_medals'] += athlete_stats['bronze_medals']

            # Собираем ID турниров
            athlete_fights = Fight.query.filter(
                ((Fight.white_athlete_id == athlete.id) | (Fight.blue_athlete_id == athlete.id)) &
                (Fight.status == 'COMPLETED')
            ).all()

            for fight in athlete_fights:
                tournament_ids.add(fight.tournament_id)

        stats['tournaments_count'] = len(tournament_ids)
        stats['win_rate'] = (stats['total_victories'] / stats['total_fights'] * 100) if stats['total_fights'] > 0 else 0

        return stats

    def get_tournament_ranking(self, tournament_id):
        """Рейтинг участников в конкретном турнире"""
        from services.result_calculator import ResultCalculator

        calculator = ResultCalculator(tournament_id)
        tournament = Tournament.query.get(tournament_id)

        rankings = []

        for category in tournament.categories:
            category_results = calculator.calculate_category_results(category.id)
            if category_results:
                for i, athlete_data in enumerate(category_results['athletes']):
                    rankings.append({
                        'position': i + 1,
                        'athlete': athlete_data['athlete'],
                        'category': category.name,
                        'victories': athlete_data['victories'],
                        'fights': athlete_data['fights'],
                        'points': athlete_data['total_points']
                    })

        return rankings

    def get_technique_statistics(self, limit=20):
        """Статистика по используемым техникам"""
        results = Result.query.filter(
            Result.technique_used.isnot(None)
        ).all()

        technique_stats = {}

        for result in results:
            technique = result.technique_used
            if technique not in technique_stats:
                technique_stats[technique] = {
                    'count': 0,
                    'success_rate': 0,
                    'total_uses': 0
                }

            technique_stats[technique]['count'] += 1
            technique_stats[technique]['total_uses'] += 1

        # Преобразуем в список и сортируем
        stats_list = [
            {
                'technique': tech,
                'count': data['count'],
                'success_rate': (data['count'] / data['total_uses'] * 100) if data['total_uses'] > 0 else 0
            }
            for tech, data in technique_stats.items()
        ]

        stats_list.sort(key=lambda x: x['count'], reverse=True)
        return stats_list[:limit]

    def export_ranking_data(self, ranking_type='athletes', format_type='CSV'):
        """Экспорт данных рейтинга"""
        if ranking_type == 'athletes':
            data = self.calculate_athlete_ranking(limit=1000)
            export_data = []

            for ranking in data:
                export_data.append({
                    'position': ranking['position'],
                    'athlete_id': ranking['athlete'].id,
                    'athlete_name': ranking['athlete'].full_name,
                    'club': ranking['athlete'].club.name if ranking['athlete'].club else '',
                    'total_points': ranking['ranking_points'],
                    'victories': ranking['stats']['victories'],
                    'fights': ranking['stats']['total_fights'],
                    'win_rate': f"{ranking['stats']['win_rate']:.1f}%",
                    'gold_medals': ranking['stats']['gold_medals'],
                    'silver_medals': ranking['stats']['silver_medals'],
                    'bronze_medals': ranking['stats']['bronze_medals']
                })

        elif ranking_type == 'clubs':
            data = self.calculate_club_ranking(limit=1000)
            export_data = []

            for ranking in data:
                export_data.append({
                    'position': ranking['position'],
                    'club_id': ranking['club'].id,
                    'club_name': ranking['club'].name,
                    'city': ranking['club'].city or '',
                    'total_points': ranking['ranking_points'],
                    'active_athletes': ranking['stats']['active_athletes'],
                    'total_victories': ranking['stats']['total_victories'],
                    'win_rate': f"{ranking['stats']['win_rate']:.1f}%",
                    'gold_medals': ranking['stats']['gold_medals'],
                    'silver_medals': ranking['stats']['silver_medals'],
                    'bronze_medals': ranking['stats']['bronze_medals']
                })

        from utils.helpers import export_data
        return export_data(export_data, format_type)