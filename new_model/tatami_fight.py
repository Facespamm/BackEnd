from datetime import datetime

from database.db import db
from new_model.Enums import TatamiStatus


class TatamiFight(db.Model):
    __tablename__ = 'tatami_fight'

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    tatami_number = db.Column(db.Integer, nullable=False)
    fight_id = db.Column(db.Integer, db.ForeignKey('fights.id'), nullable=True)

    # Статус боя на татами
    status = db.Column(db.Enum(TatamiStatus), default=TatamiStatus.FREE)

    # Связи
    fight = db.relationship('FightNew', back_populates='tatami_fight', uselist=False)
    tournament = db.relationship('TournamentNew',back_populates='tatami_fight')
