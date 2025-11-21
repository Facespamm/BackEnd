"""
Сервис экспорта данных
"""

import json
import csv
import io
from datetime import datetime
from databse.db import db
from models.tournament import Tournament
from models.category import Category
from models.fight import Fight
from models.result import Result

class ExportService:
    """Сервис экспорта данных"""

    def __init__(self, tournament_id=None):
        self.tournament_id = tournament_id

    def export_tournament_results(self, format_type='PDF'):
        """Экспорт результатов турнира"""
        tournament = Tournament.query.get(self.tournament_id)
        if not tournament:
            return None

        data = {
            'tournament': {
                'name': tournament.name,
                'dates': f"{tournament.start_date} - {tournament.end_date}",
                'venue': tournament.venue,
                'status': tournament.status
            },
            'categories': [],
            'team_ranking': []
        }

        from services.result_calculator import ResultCalculator
        calculator = ResultCalculator(self.tournament_id)

        # Результаты по категориям
        for category in tournament.categories:
            category_results = calculator.calculate_category_results(category.id)
            if category_results:
                data['categories'].append(category_results)

        # Командный зачет
        data['team_ranking'] = calculator.calculate_team_ranking()

        # Общая статистика
        data['statistics'] = calculator.calculate_tournament_statistics()

        if format_type == 'JSON':
            return self._export_json(data)
        elif format_type == 'CSV':
            return self._export_tournament_csv(data)
        elif format_type == 'EXCEL':
            return self._export_excel(data)
        else:
            return self._export_text(data)

    def export_fight_schedule(self, format_type='CSV'):
        """Экспорт расписания схваток"""
        fights = Fight.query.filter_by(tournament_id=self.tournament_id).order_by(
            Fight.tatami, Fight.scheduled_time
        ).all()

        data = []
        for fight in fights:
            fight_data = {
                'tatami': fight.tatami,
                'fight_number': fight.fight_number,
                'round': fight.round_number,
                'white_athlete': fight.white_athlete.full_name if fight.white_athlete else 'TBD',
                'blue_athlete': fight.blue_athlete.full_name if fight.blue_athlete else 'TBD',
                'scheduled_time': fight.scheduled_time.strftime('%Y-%m-%d %H:%M') if fight.scheduled_time else '',
                'status': fight.status,
                'category': fight.category.name if fight.category else ''
            }
            data.append(fight_data)

        if format_type == 'JSON':
            return json.dumps(data, ensure_ascii=False, indent=2)
        elif format_type == 'CSV':
            return self._export_csv(data)
        else:
            return str(data)

    def export_athletes_list(self, format_type='CSV'):
        """Экспорт списка участников"""
        tournament = Tournament.query.get(self.tournament_id)
        if not tournament:
            return None

        athletes_data = []

        for category in tournament.categories:
            for athlete in category.athletes:
                athlete_data = {
                    'category': category.name,
                    'last_name': athlete.last_name,
                    'first_name': athlete.first_name,
                    'middle_name': athlete.middle_name or '',
                    'birth_date': athlete.birth_date.strftime('%Y-%m-%d'),
                    'age': athlete.age,
                    'gender': 'Мужской' if athlete.gender == 'MALE' else 'Женский',
                    'club': athlete.club.name if athlete.club else '',
                    'rank': athlete.rank or '',
                    'license_number': athlete.license_number or ''
                }
                athletes_data.append(athlete_data)

        if format_type == 'JSON':
            return json.dumps(athletes_data, ensure_ascii=False, indent=2)
        elif format_type == 'CSV':
            return self._export_csv(athletes_data)
        else:
            return str(athletes_data)

    def _export_json(self, data):
        """Экспорт в JSON"""
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    def _export_csv(self, data):
        """Экспорт в CSV"""
        if not data:
            return ""

        output = io.StringIO()
        writer = csv.writer(output)

        # Заголовки
        writer.writerow(data[0].keys())

        # Данные
        for row in data:
            writer.writerow(row.values())

        return output.getvalue()

    def _export_tournament_csv(self, data):
        """Экспорт результатов турнира в CSV"""
        output = io.StringIO()
        writer = csv.writer(output)

        # Заголовок турнира
        writer.writerow(['Турнир:', data['tournament']['name']])
        writer.writerow(['Даты:', data['tournament']['dates']])
        writer.writerow(['Место:', data['tournament']['venue']])
        writer.writerow([])

        # Результаты по категориям
        for category in data['categories']:
            writer.writerow([f"Категория: {category['category']}"])
            writer.writerow(['Место', 'Участник', 'Клуб', 'Победы', 'Схватки', 'Очки'])

            for i, athlete_data in enumerate(category['athletes']):
                athlete = athlete_data['athlete']
                writer.writerow([
                    i + 1,
                    athlete.full_name,
                    athlete.club.name if athlete.club else '',
                    athlete_data['victories'],
                    athlete_data['fights'],
                    athlete_data['total_points']
                ])

            writer.writerow([])

        # Командный зачет
        writer.writerow(['КОМАНДНЫЙ ЗАЧЕТ'])
        writer.writerow(['Место', 'Клуб', 'Очки', 'Золото', 'Серебро', 'Бронза'])

        for i, club_data in enumerate(data['team_ranking']):
            writer.writerow([
                i + 1,
                club_data['club'].name,
                club_data['total_points'],
                club_data['gold_medals'],
                club_data['silver_medals'],
                club_data['bronze_medals']
            ])

        return output.getvalue()

    def _export_excel(self, data):
        """Экспорт в Excel (упрощенная версия)"""
        # В реальной реализации здесь будет логика создания Excel файла
        # с использованием библиотеки like openpyxl или xlsxwriter
        return "Excel export not implemented yet"

    def _export_text(self, data):
        """Экспорт в текстовый формат"""
        output = []

        # Заголовок турнира
        output.append(f"ТУРНИР: {data['tournament']['name']}")
        output.append(f"ДАТЫ: {data['tournament']['dates']}")
        output.append(f"МЕСТО: {data['tournament']['venue']}")
        output.append("")

        # Результаты по категориям
        for category in data['categories']:
            output.append(f"=== {category['category']} ===")
            output.append("Место | Участник | Клуб | Победы | Очки")
            output.append("-" * 50)

            for i, athlete_data in enumerate(category['athletes']):
                athlete = athlete_data['athlete']
                output.append(
                    f"{i+1:2} | {athlete.full_name:20} | {athlete.club.name if athlete.club else '':15} | "
                    f"{athlete_data['victories']:6} | {athlete_data['total_points']:5}"
                )

            output.append("")

        return "\n".join(output)

    def generate_certificate_data(self, athlete_id, place):
        """Генерация данных для сертификата"""
        athlete = Athlete.query.get(athlete_id)
        tournament = Tournament.query.get(self.tournament_id)

        if not athlete or not tournament:
            return None

        return {
            'athlete_name': athlete.full_name,
            'tournament_name': tournament.name,
            'tournament_dates': f"{tournament.start_date} - {tournament.end_date}",
            'tournament_venue': tournament.venue,
            'place': place,
            'category': None,  # Можно добавить логику определения категории
            'club': athlete.club.name if athlete.club else '',
            'date_issued': datetime.now().strftime('%d.%m.%Y'),
            'chief_referee': tournament.chief_referee or ''
        }