from database.db import db


class DanNew(db.Model):
    __tablename__ = 'dans'

    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(100), nullable=False, unique=True)  # уровень дана, например 1-10
    description = db.Column(db.String(255), nullable=True)  # описание или требования для данного уровня