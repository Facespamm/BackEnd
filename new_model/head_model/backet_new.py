from datetime import datetime

from databse.db import db


class BracketNew(db.Model):
    __tablename__ = 'brackets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    bracket_type = db.Column(db.String(20),
                             default='SINGLE_ELIMINATION')  # SINGLE_ELIMINATION, DOUBLE_ELIMINATION, ROUND_ROBIN
    status = db.Column(db.String(20), default='CREATED')  # CREATED, GENERATED, LIVE, COMPLETED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    has_consolation = db.Column(db.Boolean, default=True)  # Утешительные схватки за 3 место
    max_rounds = db.Column(db.Integer, default=0)  # 0 = автоматически

    #TODO добавить связи
