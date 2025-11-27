from datetime import datetime

from config import WEIGHT_CATEGORIES
from databse.db import db

class Weighing(db.Model):
    """
    Модель взвешивания участника
    """
    __tablename__ = 'weighings'

    # Связи
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=False)

    # Результаты взвешивания
    weight = db.Column(db.Float, nullable=False)  # Вес в кг
    weight_category = db.Column(db.String(50))    # Определенная весовая категория

    # Статус
    is_valid = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)  # Заметки

    # Время взвешивания
    weighing_time = db.Column(db.DateTime, default=datetime.utcnow)

    # Связи
    tournament = db.relationship('Tournament')
    athlete = db.relationship('Athlete', back_populates='weighings')

    def __repr__(self):
        return f'<Weighing {self.athlete_id} - {self.weight}kg>'

    @property
    def is_within_limits(self):
        """Соответствует ли вес категории"""
        if not self.weight_category:
            return True

        # Получаем ограничения категории из конфига
        category_limits = None
        athlete = self.athlete

        if athlete.gender == 'MALE':
            category_limits = WEIGHT_CATEGORIES['MALE'].get(self.weight_category)
        else:
            category_limits = WEIGHT_CATEGORIES['FEMALE'].get(self.weight_category)

        if category_limits:
            min_weight, max_weight = category_limits
            return min_weight <= self.weight <= max_weight

        return True

    @property
    def status_display(self):
        """Статус для отображения"""
        if not self.is_valid:
            return "Недействительно"
        elif not self.is_within_limits:
            return "Вне категории"
        else:
            return "Успешно"

    def determine_category(self):
        """Определить весовую категорию по весу"""
        athlete = self.athlete
        if not athlete:
            return None

        categories = (WEIGHT_CATEGORIES['MALE'] if athlete.gender == 'MALE'
                     else WEIGHT_CATEGORIES['FEMALE'])

        for category_name, (min_weight, max_weight) in categories.items():
            if min_weight <= self.weight <= max_weight:
                self.weight_category = category_name
                return category_name

        # Если вес выше максимального - последняя категория
        last_category = list(categories.keys())[-1]
        if self.weight > categories[last_category][1]:
            self.weight_category = last_category
            return last_category

        return None

    def assign_to_category(self, tournament):
        """Назначить участника в категорию турнира"""
        from models.category import Category

        if not self.weight_category:
            self.determine_category()

        if not self.weight_category:
            return False

        # Ищем подходящую категорию в турнире
        category = Category.query.filter_by(
            tournament_id=tournament.id,
            name__ilike=f'%{self.weight_category}%'
        ).first()

        if category:
            category.add_athlete(self.athlete)
            return True

        return False

    @classmethod
    def get_tournament_weighings(cls, tournament_id):
        """Получить все взвешивания турнира"""
        return cls.query.filter_by(tournament_id=tournament_id).order_by(cls.weighing_time).all()

    @classmethod
    def get_athlete_weighings(cls, athlete_id, tournament_id=None):
        """Получить взвешивания участника"""
        query = cls.query.filter_by(athlete_id=athlete_id)
        if tournament_id:
            query = query.filter_by(tournament_id=tournament_id)
        return query.order_by(cls.weighing_time.desc()).all()

    def to_dict(self):
        """Преобразовать в словарь для API"""
        data = super().to_dict()
        data['athlete_name'] = self.athlete.full_name if self.athlete else None
        data['status_display'] = self.status_display
        data['category_name'] = self.weight_category
        return data

    def save_to_db(self):
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(e)  # или логгируй
            return False