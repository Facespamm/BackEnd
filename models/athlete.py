from datetime import datetime
from database.db import db
from models import BaseModel

class Athlete(BaseModel):
    """
    Модель участника турнира
    """
    __tablename__ = 'athletes'

    # Основная информация
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50))
    birth_date = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # MALE/FEMALE

    # Спортивная информация
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'))
    rank = db.Column(db.String(20))  # КЮ/ДАН
    license_number = db.Column(db.String(50))  # Лицензия

    # Контактная информация
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))

    # Медицинская информация
    medical_check = db.Column(db.Boolean, default=False)
    insurance_number = db.Column(db.String(50))

    # Статус
    is_active = db.Column(db.Boolean, default=True)

    # Связи
    club = db.relationship('Club', backref=db.backref('athletes', lazy=True))
    weighings = db.relationship('Weighing', backref='athlete', lazy=True)
    fights_as_white = db.relationship('Fight', foreign_keys='Fight.white_athlete_id', backref='white_athlete')
    fights_as_blue = db.relationship('Fight', foreign_keys='Fight.blue_athlete_id', backref='blue_athlete')

    def __repr__(self):
        return f'<Athlete {self.first_name} {self.last_name}>'

    @property
    def full_name(self):
        """Полное имя участника"""
        if self.middle_name:
            return f"{self.last_name} {self.first_name} {self.middle_name}"
        return f"{self.last_name} {self.first_name}"

    @property
    def age(self):
        """Возраст участника"""
        today = datetime.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    def get_current_weight(self, tournament_id=None):
        """Получить текущий вес участника"""
        from models.weighing import Weighing
        weighing = Weighing.query.filter_by(
            athlete_id=self.id,
            tournament_id=tournament_id
        ).order_by(Weighing.created_at.desc()).first()
        return weighing.weight if weighing else None

    def get_fights_count(self, tournament_id=None):
        """Получить количество схваток"""
        query = Fight.query.filter(
            (Fight.white_athlete_id == self.id) | (Fight.blue_athlete_id == self.id)
        )
        if tournament_id:
            query = query.filter_by(tournament_id=tournament_id)
        return query.count()

    def get_victories_count(self, tournament_id=None):
        """Получить количество побед"""
        from models.result import Result
        query = Result.query.filter_by(winner_id=self.id)
        if tournament_id:
            query = query.join(Fight).filter(Fight.tournament_id == tournament_id)
        return query.count()