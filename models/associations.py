from datetime import datetime

from sqlalchemy import (
    Table, Column, Integer, String, DateTime,
    ForeignKey
)
from database.db import db

category_athletes = Table(
    'category_athletes',
    db.metadata,
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True),
    Column('athlete_id', Integer, ForeignKey('athletes.id'), primary_key=True),
    Column('registered_at', DateTime, default=datetime.utcnow),
)

user_roles = Table(
    'user_roles',
    db.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
)

referee_tournament = Table(
    'referee_tournament',
    db.metadata,
    Column('referee_id', Integer, ForeignKey('referees.id'), primary_key=True),
    Column('tournament_id', Integer, ForeignKey('tournaments.id'), primary_key=True),
    Column('status', String(200), nullable=False, server_default='assigned'),  # или default='assigned'
    Column('assigned_at', DateTime, default=datetime.utcnow),
)