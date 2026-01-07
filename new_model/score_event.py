from datetime import datetime

from databse.db import db


class ScoreEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fight_id = db.Column(db.Integer, db.ForeignKey('fights.id'))
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'))
    athlete_color = db.Column(db.String(5))  # WHITE / BLUE

    event_type = db.Column(db.String(20))
    # SCORE, PENALTY, OSAEKOMI_START, OSAEKOMI_STOP

    score_type = db.Column(db.String(20))
    # YUKO, WAZAARI, IPPON, SHIDO

    points = db.Column(db.Integer, default=0)
    technique = db.Column(db.String(100))

    match_time = db.Column(db.Integer)  # секунда боя
    created_at = db.Column(db.DateTime, default=datetime.utcnow)