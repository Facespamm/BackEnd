from datetime import datetime

from databse.db import db


class TournamentNew(db.Model):
    """
    Модель турнира
    """
    __tablename__ = 'tournaments'

    # Основная информация
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
    status = db.Column(db.String(20), default='PLANNED')  # PLANNED, REGISTRATION, WEIGHING, BRACKETS, LIVE, COMPLETED, CANCELLED
    is_public = db.Column(db.Boolean, default=True)

    # Организационная информация
    organizer = db.Column(db.String(100))
    chief_referee = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(100))

    # Связи
    categories = db.relationship('Category', back_populates='tournament', lazy=True, cascade='all, delete-orphan')
    fights = db.relationship('Fight', back_populates='tournament', lazy=True)
    brackets = db.relationship('Bracket', back_populates='tournament')
    referees = db.relationship('Referee', secondary='referee_tournament', back_populates='tournaments')