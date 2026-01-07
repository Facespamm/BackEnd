from datetime import datetime

from databse.db import db


class FightNew(db.Model):
    __tablename__ = 'fights'

    id = db.Column(db.Integer, primary_key=True)
    bracket_id = db.Column(db.Integer, db.ForeignKey('brackets.id'))
    white_athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'))
    blue_athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'))

    # Информация о схватке
    tatami_number = db.Column(db.Integer, default=1)
    round_number = db.Column(db.Integer, default=1)  # Раунд в сетке
    fight_number = db.Column(db.Integer)  # Номер схватки

    # Статус схватки
    status = db.Column(db.String(20), default='SCHEDULED')  # SCHEDULED, LIVE, COMPLETED, CANCELLED, REPLAY
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

    # Судьи
    main_referee = db.Column(db.String(100))
    judge_second = db.Column(db.String(100))
    judge_third = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    #TODO добавить связи