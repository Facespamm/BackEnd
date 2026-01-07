from datetime import datetime

from databse.db import db
from new_model.new_associations import new_user_roles


class UserNew(db.Model):
    """
    Модель пользователя системы
    """
    __tablename__ = 'users'

    # Учетные данные
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Информация о пользователе
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))

    # role = db.Column(db.String(20), nullable=False, default='VIEWER')  # ADMIN, REFEREE, SCOREBOARD, VIEWER
    is_active = db.Column(db.Boolean, default=True)

    # Связи
    referees = db.relationship('Referee', back_populates='user')
    roles = db.relationship('Role', secondary=new_user_roles, back_populates='users')
    athlete_profile = db.relationship('Athlete', back_populates='user')