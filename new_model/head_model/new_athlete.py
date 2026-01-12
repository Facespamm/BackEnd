from datetime import datetime

from databse.db import db
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

    #TODO добавить связи
    rank = db.relationship('DanNew')
    club = db.relationship('ClubNew', back_populates='athletes' )
    user = db.relationship('UserNew', back_populates='athlete_profile')
    categories = db.relationship('CategoryNew',
                                 secondary=new_category_athletes,  # Используем объект таблицы
                                 lazy='subquery',
                                 backref=db.backref('athletes', lazy=True))