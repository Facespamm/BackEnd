from uuid import UUID

from database.db import db, create_session
from models.associations import user_roles


class Role(db.Model):
    """Модель роли пользователя"""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    normalized_name = db.Column(db.String(50), unique=True, nullable=False)

    #связ
    users = db.relationship('User', secondary=user_roles, back_populates='roles')

    def __init__(self, name):
        self.name = name
        self.normalized_name = name.upper()


    def create_role(self):
        """Создание роли в базе данных"""
        session = create_session()
        session.add(self)
        session.commit()

    def delete_role(self):
        """Удаление роли из базы данных"""
        session = create_session()
        session.delete(self)
        session.commit()