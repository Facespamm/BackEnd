from database.db import db
from new_model.Enums import RefereeLevels


class RefereeNew(db.Model):
    __tablename__ = 'referees'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50))
    email = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    certification_level = db.Column(db.Enum(RefereeLevels))  # NATIONAL, INTERNATIONAL, etc.
    tatami_assigned = db.Column(db.Integer, nullable=True)
    #связи
    fight_referees = db.relationship('FightReferee', back_populates='referees')
    tournament = db.relationship('TournamentNew', back_populates='chief_referee')