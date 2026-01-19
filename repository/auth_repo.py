import hashlib

from sqlalchemy import select, insert

from database.db import create_session
from new_model.handbook.role_new import RoleNew
from new_model.head_model.new_user import UserNew
from new_model.new_associations import new_user_roles
from utils.security import hash_password


class AuthRepository:
    def __init__(self):
        self.session = create_session()

    def set_user_role(self,user_id,role_id):
        """Установить роль пользователя"""
        try:
            query =(
                insert(new_user_roles)
                .values(user_id=user_id, role_id=role_id)
            )
            self.session.execute(query)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error setting user role: {e}")

    def create_user(self,  user: UserNew):
        """Создать пользователя"""
        try:
            self.session.add(user)
            self.session.commit()
            return user.id
        except Exception as e:
            self.session.rollback()
            print(f"Error creating user: {e}")
            return False

    @staticmethod
    def get_role_id(role_name: str):
        """Получить роль пользователя по его имени"""
        try:
            return RoleNew.query.filter_by(name=role_name).first().id
        except Exception as e:
            print(f"Error getting role id: {e}")

    def get_role_by_user(self,user_id: int):
        """Получить роль пользователя по его ID"""
        try:
            query = (
                select(RoleNew)
                .join(new_user_roles, RoleNew.id == new_user_roles.c.role_id)
                .filter(new_user_roles.user_id == user_id)
                .limit(1)
            )
            role = self.session.execute(query).first()
            return role

        except Exception as e:
            print(f"Error getting role by user: {e}")
            return None

    def update_user_role(self, user_id, user_role_id):
        """Обновить роль пользователя"""
        try:
            user_role = self.session.query(new_user_roles).filter_by(user_id=user_id, is_active=True).first()

            if user_role:
                user_role.role_id = user_role_id
                self.session.commit()
                return True

            return False
        except Exception as e:
            self.session.rollback()
            print(f"Error updating user role: {e}")
            return False

    def get_user_by_username(self, username: str):
        """Получить пользователя по его имени"""
        try:
            return self.session.query(UserNew).filter_by(username=username, is_active=True).first()
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None

    def check_password(self,user: UserNew,password: str):
        return user.password_hash == hash_password(password)

    def hash_password(self, password):
        salt = 'judo_tournament_salt_2024'
        return hashlib.sha256((password + salt).encode()).hexdigest()
