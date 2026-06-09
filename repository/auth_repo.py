from sqlalchemy import insert, select

from database.db import get_session
from models.new_associations import new_user_roles
from models.new_user import UserNew
from models.role_new import RoleNew
from routers.auth.schemas import UpdateUserRequest


class AuthRepository:
    def __init__(self, session=None):
        self.session = session if session else get_session()
        self._owns_session = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._owns_session:
            return
        if exc_type is not None:
            self.session.rollback()
        self.session.close()

    def set_user_role(self, user_id, role_id):
        try:
            self.session.execute(
                insert(new_user_roles).values(user_id=user_id, role_id=role_id)
            )
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error setting user role: {e}")
            return False

    def create_user(self, user: UserNew):
        try:
            self.session.add(user)
            self.session.commit()
            return user.id
        except Exception as e:
            self.session.rollback()
            print(f"Error creating user: {e}")
            return False

    def get_role_id(self, role_name: str):
        """Получить ID роли по имени"""
        try:
            role = self.session.query(RoleNew).filter(RoleNew.name == role_name).first()
            if role:
                return role.id
            print(f"Роль не найдена: {role_name}")
            return None
        except Exception as e:
            print(f"Error getting role id: {e}")
            return None

    def get_role_by_user(self, user_id: int):
        try:
            query = (
                select(RoleNew)
                .join(new_user_roles, RoleNew.id == new_user_roles.c.role_id)
                .filter(new_user_roles.c.user_id == user_id)
                .limit(1)
            )
            return self.session.execute(query).scalar_one_or_none()
        except Exception as e:
            print(f"Error getting role by user: {e}")
            return None

    def update_user_role(self, user_id, user_role_id):
        try:
            result = (
                self.session.query(new_user_roles)
                .filter_by(user_id=user_id)
                .update({"role_id": user_role_id})
            )
            self.session.commit()
            return result > 0
        except Exception as e:
            self.session.rollback()
            print(f"Error updating user role: {e}")
            return False

    def get_user_by_username(self, username: str):
        try:
            return (
                self.session.query(UserNew)
                .filter_by(username=username, is_active=True)
                .first()
            )
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None

    def get_users(self):
        return (
            self.session.query(UserNew, RoleNew.name.label("role_name"))
            .join(new_user_roles, UserNew.id == new_user_roles.c.user_id)
            .filter(UserNew.is_active == True)
            .order_by(UserNew.username)
            .all()
        )

    def get_user_by_id(self, user_id: int):
        try:
            return (
                self.session.query(UserNew)
                .filter_by(id=user_id, is_active=True)
                .first()
            )
        except Exception as e:
            print(f"Error getting user by id: {e}")
            return None

    def update_user(self, existing_user: UserNew, update_data: UpdateUserRequest):
        try:
            existing_user.first_name = (
                update_data.first_name or existing_user.first_name
            )
            existing_user.last_name = update_data.last_name or existing_user.last_name
            existing_user.middle_name = (
                update_data.middle_name or existing_user.middle_name
            )
            existing_user.email = update_data.email or existing_user.email
            existing_user.phone = update_data.phone or existing_user.phone
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error updating user: {e}")
            return False

    def get_user_by_email(self, email: str):
        try:
            return (
                self.session.query(UserNew)
                .filter_by(email=email, is_active=True)
                .first()
            )
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
