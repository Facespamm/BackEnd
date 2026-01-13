"""
Сервис управления взвешиванием
"""

from config import Config
from database.db import db
from models.weighing import Weighing


class WeighingService:
    """Сервис управления взвешиванием"""

    def __init__(self, tournament_id):
        self.tournament_id = tournament_id

    def toggle_validation_status(self, weighing_id):
        """Изменить статус валидации взвешивания (валидно/невалидно)"""
        weighing = Weighing.query.get(weighing_id)
        if not weighing:
            return {
                'success': False,
                'message': 'Взвешивание не найдено'
            }

        # Меняем статус на противоположный
        weighing.is_valid = not weighing.is_valid

        try:
            db.session.commit()
            return {
                'success': True,
                'message': f'Статус валидации изменен на {"валидно" if weighing.is_valid else "невалидно"}',
                'is_valid': weighing.is_valid
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Ошибка при изменении статуса: {str(e)}'
            }

    def register_weighing(self, athlete_id, weight, weight_category=None, notes=None):
        """Зарегистрировать взвешивание"""
        # Проверяем существующее взвешивание
        existing = Weighing.query.filter_by(
            tournament_id=self.tournament_id,
            athlete_id=athlete_id
        ).first()

        if existing:
            # Обновляем существующее
            existing.weight = weight
            existing.notes = notes

            # Если указана категория вручную - используем ее
            if weight_category:
                existing.weight_category = weight_category
            else:
                existing.determine_category()

            return existing.save()
        else:
            # Создаем новое
            weighing = Weighing(
                tournament_id=self.tournament_id,
                athlete_id=athlete_id,
                weight=weight,
                notes=notes
            )

            # Если указана категория вручную - используем ее
            if weight_category:
                weighing.weight_category = weight_category
            else:
                # Определяем категорию автоматически
                weighing.determine_category()

            db.session.add(weighing)
            return weighing.save()
    def assign_to_categories(self):
        """Автоматическое распределение участников по категориям"""
        weighings = Weighing.query.filter_by(
            tournament_id=self.tournament_id,
            is_valid=True
        ).all()

        assigned_count = 0
        errors = []

        for weighing in weighings:
            try:
                if weighing.assign_to_category(weighing.tournament):
                    assigned_count += 1
            except Exception as e:
                errors.append(f"Ошибка назначения {weighing.athlete.full_name}: {str(e)}")

        return {
            'assigned_count': assigned_count,
            'total_weighings': len(weighings),
            'errors': errors
        }

    def get_weighing_statistics(self):
        """Получить статистику взвешивания"""
        weighings = Weighing.query.filter_by(tournament_id=self.tournament_id).all()

        stats = {
            'total_weighed': len(weighings),
            'valid_weighings': 0,
            'invalid_weighings': 0,
            'within_limits': 0,
            'out_of_limits': 0,
            'categories_distribution': {},
            'gender_distribution': {
                'MALE': 0,
                'FEMALE': 0
            }
        }

        for weighing in weighings:
            if weighing.is_valid:
                stats['valid_weighings'] += 1
            else:
                stats['invalid_weighings'] += 1

            if weighing.is_within_limits:
                stats['within_limits'] += 1
            else:
                stats['out_of_limits'] += 1

            # Распределение по категориям
            if weighing.weight_category:
                if weighing.weight_category not in stats['categories_distribution']:
                    stats['categories_distribution'][weighing.weight_category] = 0
                stats['categories_distribution'][weighing.weight_category] += 1

            # Распределение по полу
            if weighing.athlete.gender in stats['gender_distribution']:
                stats['gender_distribution'][weighing.athlete.gender] += 1

        return stats

    def validate_weighing(self, weighing_id, is_valid=True):
        """Валидация/инвалидация взвешивания"""
        weighing = Weighing.query.get(weighing_id)
        if not weighing:
            return False

        weighing.is_valid = is_valid
        return weighing.save()

    def get_athletes_without_weighing(self):
        """Получить участников без взвешивания"""
        from models.tournament import Tournament

        tournament = Tournament.query.get(self.tournament_id)
        if not tournament:
            return []

        # Получаем всех участников турнира
        all_athletes = []
        for category in tournament.categories:
            all_athletes.extend(category.athletes)

        # Получаем участников с взвешиванием
        weighed_athlete_ids = [
            w.athlete_id for w in Weighing.query.filter_by(tournament_id=self.tournament_id).all()
        ]

        # Находим участников без взвешивания
        athletes_without_weighing = [
            athlete for athlete in all_athletes 
            if athlete.id not in weighed_athlete_ids
        ]

        return athletes_without_weighing

    def export_weighing_data(self, format_type='CSV'):
        """Экспорт данных взвешивания"""
        weighings = Weighing.query.filter_by(tournament_id=self.tournament_id).all()

        data = []
        for weighing in weighings:
            data.append({
                'athlete_id': weighing.athlete_id,
                'athlete_name': weighing.athlete.full_name,
                'club': weighing.athlete.club.name if weighing.athlete.club else '',
                'gender': weighing.athlete.gender,
                'weight': weighing.weight,
                'weight_category': weighing.weight_category or '',
                'is_valid': 'Да' if weighing.is_valid else 'Нет',
                'within_limits': 'Да' if weighing.is_within_limits else 'Нет',
                'weighing_time': weighing.weighing_time.strftime('%Y-%m-%d %H:%M'),
                'notes': weighing.notes or ''
            })

        from utils.helpers import export_data
        return export_data(data, format_type)

    def get_category_suggestions(self, athlete_id):
        """Получить предложения по категориям для участника"""
        athlete = Weighing.query.get(athlete_id).athlete
        if not athlete:
            return []

        categories = []
        weight_categories = (Config.WEIGHT_CATEGORIES['MALE'] if athlete.gender == 'MALE' 
                           else Config.WEIGHT_CATEGORIES['FEMALE'])

        for category_name, (min_weight, max_weight) in weight_categories.items():
            categories.append({
                'name': category_name,
                'range': f"{min_weight}-{max_weight}кг",
                'min_weight': min_weight,
                'max_weight': max_weight
            })

        return categories