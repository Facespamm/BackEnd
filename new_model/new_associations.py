from datetime import datetime

from sqlalchemy import (
    Table, Column, Integer, String, DateTime,
    ForeignKey
)
from database.db import db
from new_model.Enums import ConsolationType

new_user_roles = Table(
    'new_user_roles',
    db.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
)

class TournamentCategory(db.Model):
    __tablename__ = 'new_tournament_categories'

    tournament_category_id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    has_consolidation_fights = db.Column(db.Boolean, default=False)

    # Relationships
    tournament = db.relationship('TournamentNew', back_populates='tournament_categories')
    category = db.relationship('CategoryNew', back_populates='tournament_categories')
    registrations = db.relationship('AthleteRegistration', back_populates='tournament_categories')


class AthleteRegistration(db.Model):
    __tablename__ = 'new_athlete_tournament'

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=False)
    tournament_category_id = db.Column(db.Integer, db.ForeignKey('new_tournament_categories.tournament_category_id'))
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    athlete = db.relationship('AthleteNew', back_populates='registrations')
    tournament_categories = db.relationship('TournamentCategory', back_populates='registrations')


class FightReferee(db.Model):
    __tablename__ = 'fight_referee'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fight_id = db.Column(db.Integer, db.ForeignKey('fights.id'), nullable=False)
    referee_id = db.Column(db.Integer, db.ForeignKey('referees.id'), nullable=False)
    role = db.Column(db.String(20))  # MAIN, SECOND, THIRD

    # Relationships
    fight = db.relationship('FightNew', back_populates='fight_referees')
    referees = db.relationship('RefereeNew', back_populates='fight_referees')