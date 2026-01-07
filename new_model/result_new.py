from databse.db import db


class ResultNew(db.Model):
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True)
    fight_id = db.Column(db.Integer, db.ForeignKey('fights.id'), nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=False)
    victory_type = db.Column(db.String(100), nullable=False)
    fight_duration = db.Column(db.Float, nullable=False)

    # TODO добавить связи