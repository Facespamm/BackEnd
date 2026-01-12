from databse.db import db
from new_model.new_associations import new_user_roles


class RoleNew(db.Model):
    """Модель роли пользователя"""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    normalized_name = db.Column(db.String(50), unique=True, nullable=False)

    #связ
    users = db.relationship('UserNew', secondary=new_user_roles, back_populates='roles')