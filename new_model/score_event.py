from datetime import datetime

from database.db import db
from models.Enums import AthleteColor, EventType, ScoreType


class ScoreEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fight_id = db.Column(db.Integer, db.ForeignKey('fights.id'))
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'))
    athlete_color = db.Column(db.Enum(AthleteColor))

    event_type = db.Column(db.Enum(EventType))
    score_type = db.Column(db.Enum(ScoreType))
    points = db.Column(db.Integer, default=0)
    technique = db.Column(db.String(100))

    match_time = db.Column(db.Integer)  # секунда боя
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    #Связи
    fight = db.relationship('FightNew', back_populates='score_events')
    athlete = db.relationship('AthleteNew')