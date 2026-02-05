from datetime import datetime

from database.db import db
from new_model.Enums import FightStatus, BracketType


class FightNew(db.Model):
    __tablename__ = 'fights'

    id = db.Column(db.Integer, primary_key=True)
    tournament_category_id = db.Column(db.Integer,db.ForeignKey('new_tournament_categories.tournament_category_id'),nullable=False)
    white_athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=True)
    blue_athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=True)

    # Информация о схватке
    tatami_number = db.Column(db.Integer, default=0)
    round_number = db.Column(db.Integer, default=1)  # Раунд в сетке
    fight_number = db.Column(db.Integer)  # Номер схватки

    # Статус схватки
    status = db.Column(db.Enum(FightStatus), default=FightStatus.SCHEDULED)
    start_time = db.Column(db.Interval)
    end_time = db.Column(db.Interval)
    next_fight_id  = db.Column(db.Integer, default=None, nullable=True) #Ссылка на следующию схватку в сетке
    type_bracket = db.Column(db.Enum(BracketType), default='MAIN')  # Тип сетки для разделения боев

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    #Связи
    white_athlete = db.relationship('AthleteNew', back_populates='white_fights', foreign_keys=[white_athlete_id])
    blue_athlete = db.relationship('AthleteNew', back_populates='blue_fights', foreign_keys=[blue_athlete_id])
    fight_referees = db.relationship('FightReferee', back_populates='fight')
    score_events = db.relationship('ScoreEvent', back_populates='fight')
    result = db.relationship('ResultNew', back_populates='fight', uselist=False)
    tatami_fight = db.relationship('TatamiFight', back_populates='fight', uselist=False)