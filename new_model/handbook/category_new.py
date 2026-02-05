from datetime import datetime

from database.db import db
from new_model.Enums import Gender

class CategoryNew(db.Model):
    __tablename__ = 'categories'

    # Связь с турниром
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.Enum(Gender), nullable=False)
    min_weight = db.Column(db.Float)
    max_weight = db.Column(db.Float, nullable=True)
    min_year = db.Column(db.Integer)
    max_year = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    #связи
    tournament_categories = db.relationship('TournamentCategory', lazy = True ,back_populates='category')
    weighings = db.relationship('WeighingNew', back_populates='category')
    athletes = db.relationship('AthleteNew',
                               lazy=True,
                               back_populates='categories')