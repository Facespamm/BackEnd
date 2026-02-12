from datetime import datetime

from database.db import db
from new_model.Enums import StatusTournament


class TournamentNew(db.Model):
    """
    Модель турнира
    """
    __tablename__ = 'tournaments'

    # Основная информация
    id = db.Column(db.Integer, primary_key=True)
    #category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    # Даты проведения
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    registration_deadline = db.Column(db.Date)

    # Место проведения
    venue = db.Column(db.String(200))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    country = db.Column(db.String(50), default='Россия')

    # Настройки турнира
    max_athletes = db.Column(db.Integer, default=0)  # 0 = без ограничений
    tatami_count = db.Column(db.Integer, default=1)
    fight_duration = db.Column(db.Integer, default=300)  # в секундах
    golden_score_duration = db.Column(db.Integer, default=180)  # в секундах

    # Статус турнира
    status = db.Column(db.Enum(StatusTournament), default=StatusTournament.PLANNED)
    is_public = db.Column(db.Boolean, default=True)

    has_consolation_fights = db.Column(db.Boolean, default=False)
    # Организационная информация
    organizer = db.Column(db.String(100))
    chief_referee_id = db.Column(db.Integer, db.ForeignKey('referees.id'))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    tournament_categories = db.relationship('TournamentCategory',
        lazy=True,
        back_populates='tournament')
    # fights = db.relationship('FightNew', back_populates='tournament')
    chief_referee = db.relationship('RefereeNew', back_populates='tournament')
    tatami_fight = db.relationship('TatamiFight', back_populates='tournament')