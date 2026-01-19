from datetime import datetime

from sqlalchemy import (
    Table, Column, Integer, String, DateTime,
    ForeignKey
)
from database.db import db

new_category_athletes = Table(
    'new_category_athletes',
    db.metadata,
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True),
    Column('athlete_id', Integer, ForeignKey('athletes.id'), primary_key=True),
)

new_user_roles = Table(
    'new_user_roles',
    db.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
)

# new_referee_tournament = Table(
#     'referee_tournament',
#     db.metadata,
#     Column('referee_id', Integer, ForeignKey('referees.id'), primary_key=True),
#     Column('tournament_id', Integer, ForeignKey('tournaments.id'), primary_key=True),
#     Column('status', String(200), nullable=False, server_default='assigned'),  # или default='assigned'
# )

fight_referee = db.Table('new_fight_referee',
    db.Column('fight_id', db.Integer, db.ForeignKey('fights.id')),
    db.Column('referee_id', db.Integer, db.ForeignKey('referees.id')),
    db.Column('role', db.String(20))  # MAIN, SECOND, THIRD
)

athlete_tournament = db.Table('new_athlete_tournament',
    db.Column('athlete_id', db.Integer, db.ForeignKey('athletes.id')),
    db.Column('tournament_id', db.Integer, db.ForeignKey('tournaments.id')),
    db.Column('registration_date', db.DateTime, default=datetime.utcnow)
)

tournament_categories = db.Table(
    'new_tournament_categories',
    db.Column('tournament_id', db.Integer, db.ForeignKey('tournaments.id')),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'))
)