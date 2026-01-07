from datetime import datetime

from databse.db import db
from models.Enums import Gender
from new_model.new_associations import new_category_athletes


class CategoryNew(db.Model):
    __tablename__ = 'categories'

    # Связь с турниром
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    gender = db.Column(db.Enum(Gender), nullable=False)
    min_weight = db.Column(db.Float)
    max_weight = db.Column(db.Float)
    min_age = db.Column(db.Integer)
    max_age = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # TODO добавить связи
    athletes = db.relationship('AthleteNew',
                               secondary=new_category_athletes,  # Используем объект таблицы
                               lazy='subquery',
                               backref=db.backref('categories', lazy=True))