from datetime import datetime

from database.db import db
from models.Enums import FightStatus
from new_model.new_associations import fight_referee


class FightNew(db.Model):
    __tablename__ = 'fights'

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
    white_athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'))
    blue_athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'))

    # Информация о схватке
    tatami_number = db.Column(db.Integer, default=0)
    round_number = db.Column(db.Integer, default=1)  # Раунд в сетке
    fight_number = db.Column(db.Integer)  # Номер схватки

    # Статус схватки
    status = db.Column(db.Enum(FightStatus), default=FightStatus.SCHEDULED)  # SCHEDULED, LIVE, COMPLETED, CANCELLED, REPLAY
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    #Связи
    tournament = db.relationship('TournamentNew', back_populates='fights')
    white_athlete = db.relationship('AthleteNew', back_populates='white_fights', foreign_keys=[white_athlete_id])
    blue_athlete = db.relationship('AthleteNew', back_populates='blue_fights', foreign_keys=[blue_athlete_id])
    referees = db.relationship('RefereeNew', secondary=fight_referee, back_populates='fights')
    score_events = db.relationship('ScoreEvent', back_populates='fight')
    result = db.relationship('ResultNew', back_populates='fight', uselist=False)