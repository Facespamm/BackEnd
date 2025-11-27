from databse.db import db


class Dan(db.Model):
    """Модель данов"""
    __tablename__ = 'dans'

    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.Integer, nullable=False, unique=True)  # уровень дана, например 1-10
    description = db.Column(db.String(255), nullable=True)  # описание или требования для данного уровня
    #Связи
    athletes = db.relationship('Athlete', back_populates='rank', lazy='dynamic')

    def __repr__(self):
        return f'<Dan {self.level}>'