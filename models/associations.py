from datetime import datetime
from database.db import db

# Таблица связи многие-ко-многим для участников и категорий
category_athletes = db.Table('category_athletes',
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True),
    db.Column('athlete_id', db.Integer, db.ForeignKey('athletes.id'), primary_key=True),
    db.Column('registered_at', db.DateTime, default=datetime.utcnow)
)