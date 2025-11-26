from sqlalchemy import ForeignKey
from sqlalchemy.orm.sync import update

from databse.db import db, create_session

class Referee(db.Model):
    """Модель судьи"""
    __tablename__ = 'referees'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    certification_level = db.Column(db.String(50), nullable=True) # NATIONAL, INTERNATIONAL, etc.
    tatami_assigned = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    #TODO: добавить связь с турнирами и пользователем, когда соответствующие модели будут готовы
    #связь
    user = db.relationship('User', back_populates='referees')
    tournaments = db.relationship('Tournament', secondary='referee_tournament', back_populates='referees')

    def __init__(self, name, certification_level=None):
        self.name = name
        self.certification_level = certification_level

    def create(self):
        """Создание судьи в базе данных"""
        session = create_session()
        session.add(self)
        session.commit()

    def update(self):
        """Обновление информации о судье"""
        stmt = (
            update(Referee)
            .values(name=self.name, certification_level=self.certification_level)
            .filter_by(id=self.id)
        )
        session = create_session()
        session.execute(stmt)
        session.commit()

    def delete(self):
        """Удаление судьи из базы данных"""
        session = create_session()
        session.delete(self)
        session.commit()