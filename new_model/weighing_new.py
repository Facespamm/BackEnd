from datetime import datetime

from database.db import db


class WeighingNew(db.Model):
    __tablename__ = 'weighings'

    # Связи
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)  # Вес в кг
    is_valid = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)  # Заметки
    weighing_time = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    #Связи
    tournament = db.relationship('TournamentNew', back_populates='weighings')
    athlete = db.relationship('AthleteNew', back_populates='weighings')