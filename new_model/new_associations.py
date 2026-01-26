from datetime import datetime

from sqlalchemy import (
    Table, Column, Integer, String, DateTime,
    ForeignKey
)
from database.db import db

new_user_roles = Table(
    'new_user_roles',
    db.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
)

# fight_referee = db.Table('new_fight_referee',
#     db.Column('fight_id', db.Integer, db.ForeignKey('fights.id')),
#     db.Column('referee_id', db.Integer, db.ForeignKey('referees.id')),
#     db.Column('role', db.String(20))  # MAIN, SECOND, THIRD
# )
#
# athlete_tournament = db.Table('new_athlete_tournament',
#     db.Column('athlete_id', db.Integer, db.ForeignKey('athletes.id')),
#     db.Column('tournament_category_id', db.Integer, db.ForeignKey('new_tournament_categories.tournament_category_id')),
#     db.Column('registration_date', db.DateTime, default=datetime.utcnow)
# )
#
# tournament_categories = db.Table(
#     'new_tournament_categories',
#     db.Column('tournament_category_id', db.Integer, primary_key=True),
#     db.Column('tournament_id', db.Integer, db.ForeignKey('tournaments.id')),
#     db.Column('category_id', db.Integer, db.ForeignKey('categories.id'))
# )

class TournamentCategory(db.Model):
    __tablename__ = 'new_tournament_categories'

    tournament_category_id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

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