from database.db import db
from models.base import BaseModel
from datetime import datetime

class Category(BaseModel):
    """
    Модель весовой категории
    """
    __tablename__ = 'categories'

    # Связь с турниром
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)

    # Информация о категории
    name = db.Column(db.String(50), nullable=False)  # Например: "Мужчины до 73кг"
    gender = db.Column(db.String(10), nullable=False)  # MALE/FEMALE
    min_weight = db.Column(db.Float)  # Минимальный вес (кг)
    max_weight = db.Column(db.Float)  # Максимальный вес (кг)
    min_age = db.Column(db.Integer)   # Минимальный возраст
    max_age = db.Column(db.Integer)   # Максимальный возраст

    # Статус
    is_active = db.Column(db.Boolean, default=True)

    # Связи
    brackets = db.relationship('Bracket', backref='category', lazy=True, cascade='all, delete-orphan')
    athletes = db.relationship('Athlete', secondary='category_athletes', lazy='subquery',
                              backref=db.backref('categories', lazy=True))

    def __repr__(self):
        return f'<Category {self.name}>'

    @property
    def athletes_count(self):
        """Количество участников в категории"""
        return len(self.athletes)

    @property
    def weight_range(self):
        """Диапазон веса в текстовом формате"""
        if self.min_weight and self.max_weight:
            return f"{self.min_weight}-{self.max_weight}кг"
        elif self.min_weight:
            return f"свыше {self.min_weight}кг"
        elif self.max_weight:
            return f"до {self.max_weight}кг"
        return "Любой вес"

    @property
    def age_range(self):
        """Диапазон возраста в текстовом формате"""
        if self.min_age and self.max_age:
            return f"{self.min_age}-{self.max_age} лет"
        elif self.min_age:
            return f"старше {self.min_age} лет"
        elif self.max_age:
            return f"младше {self.max_age} лет"
        return "Любой возраст"

    def add_athlete(self, athlete):
        """Добавить участника в категорию"""
        if athlete not in self.athletes:
            self.athletes.append(athlete)
            return True
        return False

    def remove_athlete(self, athlete):
        """Удалить участника из категории"""
        if athlete in self.athletes:
            self.athletes.remove(athlete)
            return True
        return False

    def get_bracket(self):
        """Получить турнирную сетку категории"""
        return Bracket.query.filter_by(category_id=self.id).first()

    def get_completed_fights_count(self):
        """Получить количество завершенных схваток в категории"""
        from models.fight import Fight
        bracket = self.get_bracket()
        if bracket:
            return Fight.query.filter_by(
                bracket_id=bracket.id,
                status='COMPLETED'
            ).count()
        return 0

# Таблица связи многие-ко-многим для участников и категорий
category_athletes = db.Table('category_athletes',
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True),
    db.Column('athlete_id', db.Integer, db.ForeignKey('athletes.id'), primary_key=True),
    db.Column('registered_at', db.DateTime, default=datetime.utcnow)
)