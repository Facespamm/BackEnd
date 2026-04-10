from datetime import datetime

from database.db import db
from new_model.Enums import StatusTournamentRegistration

class AthleteTournamentRegistration(db.Model):
    __tablename__ = 'athlete_tournament_registration'

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)

    # Дополнительно полезные поля:
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum(StatusTournamentRegistration), default=StatusTournamentRegistration.REGISTERED)  # registered, weighed_in, cancelled

    # Кто зарегистрировал (админ или сам спортсмен)
    registered_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    athlete = db.relationship('AthleteNew', back_populates='athlete_tournament_registration')
    tournament = db.relationship('TournamentNew', back_populates='registrations')
