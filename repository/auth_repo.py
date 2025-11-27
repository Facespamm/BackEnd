from sqlalchemy import select, insert
from sqlalchemy.orm import selectinload

from databse.db import create_session
from models.associations import user_roles
from models.role import Role
from models.user import User


class AuthRepository:
    def __init__(self):
        self.session = create_session()

    def set_user_role(self,user_id,role_id):
        """Установить роль пользователя"""
        try:
            query =(
                insert(user_roles)
                .values(user_id=user_id, role_id=role_id)
            )
            self.session.execute(query)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error setting user role: {e}")

    def create_user(self,  user: User):
        """Создать пользователя"""
        try:
            self.session.add(user)
            self.session.commit()
            return user.id
        except Exception as e:
            self.session.rollback()
            print(f"Error creating user: {e}")
            return False

    def get_role_id(self,role_name: str):
        """Получить роль пользователя по его имени"""
        try:
            return Role.query.filter_by(name=role_name).first().id
        except Exception as e:
            print(f"Error getting role id: {e}")

    def get_role_by_user(self,user_id: int):
        """Получить роль пользователя по его ID"""
        try:
            query = (
                select(Role)
                .join(user_roles, Role.id == user_roles.c.role_id)
                .where(user_roles.c.user_id == user_id)
                .limit(1)
            )
            role = self.session.execute(query).scalar_one_or_none()
            return role

        except Exception as e:
            print(f"Error getting role by user: {e}")
            return None