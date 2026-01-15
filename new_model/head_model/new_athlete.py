from datetime import datetime

from database.db import db
from new_model.head_model.fight_new import FightNew
from new_model.new_associations import new_category_athletes


class AthleteNew(db.Model):
    __tablename__ = 'athletes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'))
    birth_date = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    rank_id = db.Column(db.Integer, db.ForeignKey('dans.id'))  # КЮ/ДАН
    license_number = db.Column(db.String(50))
    medical_check = db.Column(db.Boolean, default=False)
    insurance_number = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    #связи
    rank = db.relationship('DanNew')
    club = db.relationship('ClubNew', back_populates='athletes' )
    user = db.relationship('UserNew', back_populates='athlete_profile')
    weighings = db.relationship('WeighingNew', back_populates='athlete')

    white_fights = db.relationship('FightNew',
                                   back_populates='white_athlete',
                                   foreign_keys=[FightNew.white_athlete_id])

    blue_fights = db.relationship('FightNew',
                                  back_populates='blue_athlete',
                                  foreign_keys=[FightNew.blue_athlete_id])

    categories = db.relationship('CategoryNew',
                                 secondary=new_category_athletes,  # Используем объект таблицы
                                 lazy=True,
                                 backref=db.backref('athletes'))

    tournaments = db.relationship('TournamentNew',
                                  secondary='athlete_tournament',
                                  lazy=True,
                                  back_populates='athletes')