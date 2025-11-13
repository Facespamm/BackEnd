"""
Калькулятор результатов и рейтингов
"""

from database.db import db
from models.result import Result
from models.fight import Fight
from utils.helpers import calculate_ranking_points

class ResultCalculator:
    """Калькулятор результатов турнира"""

    def __init__(self, tournament_id):
        self.tournament_id = tournament_id

    def calculate_category_results(self, category_id):
        """Расчет результатов для категории"""
        from models.category import Category
        from models.bracket import Bracket

        category = Category.query.get(category_id)
        if not category:
            return None

        bracket = category.get_bracket()
        if not bracket:
            return None

        # Получаем все схватки категории
        fights = Fight.query.filter_by(
            tournament_id=self.tournament_id,
            category_id=category_id,
            status='COMPLETED'
        ).all()

        results = {
            'category': category.name,
            'athletes': [],
            'winner': None,
            'second_place': None,
            'third_place': None
        }

        # Собираем статистику по участникам
        athlete_stats = {}
        for athlete in category.athletes:
            athlete_stats[athlete.id] = {
                'athlete': athlete,
                'fights': 0,
                'victories': 0,
                'defeats': 0,
                'ippon_count': 0,
                'wazaari_count': 0,
                'total_points': 0,
                'quick_victories': 0
            }

        # Заполняем статистику
        for fight in fights:
            if not fight.result:
                continue

            winner_id = fight.result.winner_id
            loser_id = fight.get_loser().id if fight.get_loser() else None

            # Статистика победителя
            if winner_id in athlete_stats:
                athlete_stats[winner_id]['fights'] += 1
                athlete_stats[winner_id]['victories'] += 1
                athlete_stats[winner_id]['total_points'] += calculate_ranking_points(
                    fight.result.victory_type,
                    fight.result.fight_duration
                )

                if fight.result.is_ippon:
                    athlete_stats[winner_id]['ippon_count'] += 1
                if fight.result.is_wazaari:
                    athlete_stats[winner_id]['wazaari_count'] += 1
                if fight.result.is_quick_victory:
                    athlete_stats[winner_id]['quick_victories'] += 1

            # Статистика проигравшего
            if loser_id and loser_id in athlete_stats:
                athlete_stats[loser_id]['fights'] += 1
                athlete_stats[loser_id]['defeats'] += 1

        # Определяем места
        sorted_athletes = sorted(
            athlete_stats.values(),
            key=lambda x: (
                x['victories'],  # Количество побед
                x['ippon_count'],  # Количество иппонов
                x['total_points'],  # Общее количество очков
                x['quick_victories']  # Быстрые победы
            ),
            reverse=True
        )

        results['athletes'] = sorted_athletes

        # Определяем призеров
        if sorted_athletes:
            results['winner'] = sorted_athletes[0]['athlete'] if sorted_athletes[0]['victories'] > 0 else None

            if len(sorted_athletes) > 1 and sorted_athletes[1]['victories'] > 0:
                results['second_place'] = sorted_athletes[1]['athlete']

            if len(sorted_athletes) > 2 and sorted_athletes[2]['victories'] > 0:
                results['third_place'] = sorted_athletes[2]['athlete']

        return results

    def calculate_team_ranking(self):
        """Расчет командного зачета"""
        from models.club import Club
        from models.athlete import Athlete

        clubs = Club.query.filter_by(is_active=True).all()
        club_results = {}

        for club in clubs:
            club_results[club.id] = {
                'club': club,
                'gold_medals': 0,
                'silver_medals': 0,
                'bronze_medals': 0,
                'total_points': 0,
                'athletes_count': 0
            }

        # Получаем все завершенные схватки турнира
        fights = Fight.query.filter_by(
            tournament_id=self.tournament_id,
            status='COMPLETED'
        ).all()

        for fight in fights:
            if not fight.result:
                continue

            winner = fight.result.winner
            if winner and winner.club_id:
                club_id = winner.club_id

                # Определяем тип медали по раунду
                if fight.round_number == 1:  # Финал
                    club_results[club_id]['gold_medals'] += 1
                    club_results[club_id]['total_points'] += 10
                elif fight.round_number == 2:  # Полуфинал/за 3 место
                    club_results[club_id]['silver_medals'] += 1
                    club_results[club_id]['total_points'] += 7
                else:  # Другие места
                    club_results[club_id]['bronze_medals'] += 1
                    club_results[club_id]['total_points'] += 5

        # Подсчитываем количество участников от каждого клуба
        for club in clubs:
            athletes_count = Athlete.query.filter_by(
                club_id=club.id,
                is_active=True
            ).count()
            club_results[club.id]['athletes_count'] = athletes_count

        # Сортируем клубы по очкам
        sorted_clubs = sorted(
            club_results.values(),
            key=lambda x: (
                x['total_points'],
                x['gold_medals'],
                x['silver_medals'],
                x['bronze_medals']
            ),
            reverse=True
        )

        return sorted_clubs

    def calculate_tournament_statistics(self):
        """Расчет общей статистики турнира"""
        fights = Fight.query.filter_by(tournament_id=self.tournament_id).all()
        completed_fights = [f for f in fights if f.status == 'COMPLETED']

        stats = {
            'total_fights': len(fights),
            'completed_fights': len(completed_fights),
            'cancelled_fights': len([f for f in fights if f.status == 'CANCELLED']),
            'ippon_count': 0,
            'wazaari_count': 0,
            'shido_count': 0,
            'average_fight_duration': 0,
            'quick_victories': 0,
            'golden_score_fights': 0
        }

        total_duration = 0
        for fight in completed_fights:
            if fight.result:
                if fight.result.is_ippon:
                    stats['ippon_count'] += 1
                if fight.result.is_wazaari:
                    stats['wazaari_count'] += 1
                if fight.result.victory_type == 'SHIDO':
                    stats['shido_count'] += 1
                if fight.result.is_quick_victory:
                    stats['quick_victories'] += 1
                if fight.is_golden_score:
                    stats['golden_score_fights'] += 1

                if fight.result.fight_duration:
                    total_duration += fight.result.fight_duration

        if len(completed_fights) > 0:
            stats['average_fight_duration'] = total_duration / len(completed_fights)

        return stats

    def get_athlete_tournament_stats(self, athlete_id):
        """Получить статистику участника в турнире"""
        fights = Fight.query.filter(
            ((Fight.white_athlete_id == athlete_id) | (Fight.blue_athlete_id == athlete_id)) &
            (Fight.tournament_id == self.tournament_id)
        ).all()

        stats = {
            'total_fights': len(fights),
            'victories': 0,
            'defeats': 0,
            'ippon_victories': 0,
            'wazaari_victories': 0,
            'shido_victories': 0,
            'quick_victories': 0,
            'total_points': 0
        }

        for fight in fights:
            if fight.status == 'COMPLETED' and fight.result:
                if fight.result.winner_id == athlete_id:
                    stats['victories'] += 1
                    stats['total_points'] += calculate_ranking_points(
                        fight.result.victory_type,
                        fight.result.fight_duration
                    )

                    if fight.result.is_ippon:
                        stats['ippon_victories'] += 1
                    if fight.result.is_wazaari:
                        stats['wazaari_victories'] += 1
                    if fight.result.victory_type == 'SHIDO':
                        stats['shido_victories'] += 1
                    if fight.result.is_quick_victory:
                        stats['quick_victories'] += 1
                else:
                    stats['defeats'] += 1

        return stats