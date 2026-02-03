from datetime import datetime

from database.db import db


class WeighingNew(db.Model):
    __tablename__ = 'weighings'

    # Связи
    id = db.Column(db.Integer, primary_key=True)
    tournament_category_id = db.Column(db.Integer, db.ForeignKey('new_tournament_categories.tournament_category_id'), nullable=False)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)  # Вес в кг
    weight_category = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    is_valid = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)  # Заметки
    weighing_time = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    #Связи
    tournament_categories = db.relationship('TournamentCategory', back_populates='weighings')
    athlete = db.relationship('AthleteNew', back_populates='weighings')
    category = db.relationship('CategoryNew', back_populates='weighings')