from datetime import datetime

from database.db import db


class TatamiFight(db.Model):
    __tablename__ = 'tatami_fight'

    id = db.Column(db.Integer, primary_key=True)
    tatami_number = db.Column(db.Integer, nullable=False)
    fight_id = db.Column(db.Integer, db.ForeignKey('fights.id'), nullable=False, unique=True)

    # Статус боя на татами
    can_start = db.Column(db.Boolean, default=False, nullable=False)

    # Опционально: временные метки
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Связи
    fight = db.relationship('FightNew', back_populates='tatami_fight', uselist=False)
