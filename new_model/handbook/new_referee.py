from database.db import db

class RefereeNew(db.Model):
    __tablename__ = 'referees'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    certification_level = db.Column(db.String(50), nullable=True)  # NATIONAL, INTERNATIONAL, etc.
    tatami_assigned = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    #связи
    user = db.relationship('UserNew', back_populates='referees')
    fight_referees = db.relationship('FightReferee', back_populates='referees')
    tournament = db.relationship('TournamentNew', back_populates='chief_referee')