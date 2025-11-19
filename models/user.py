from database.db import db
from models import BaseModel
from utils.security import hash_password, check_password

class User(BaseModel):
    """
    Модель пользователя системы
    """
    __tablename__ = 'users'

    # Учетные данные
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Информация о пользователе
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))

    # Роль и права
    role = db.Column(db.String(20), nullable=False, default='VIEWER')  # ADMIN, REFEREE, SCOREBOARD, VIEWER
    is_active = db.Column(db.Boolean, default=True)

    # Специализация (для судей)
    referee_level = db.Column(db.String(20))  # NATIONAL, INTERNATIONAL, etc.
    tatami_assigned = db.Column(db.Integer)   # Назначенный татами

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

    def set_password(self, password):
        """Установить пароль"""
        self.password_hash = hash_password(password)

    def check_password(self, password):
        """Проверить пароль"""
        return check_password(self.password_hash, password)

    @property
    def is_admin(self):
        """Является ли администратором"""
        return self.role == 'ADMIN'

    @property
    def is_referee(self):
        """Является ли судьей"""
        return self.role == 'REFEREE'

    @property
    def is_scoreboard(self):
        """Имеет доступ к табло"""
        return self.role in ['ADMIN', 'SCOREBOARD']

    @property
    def role_display(self):
        """Отображаемое название роли"""
        from config import Config
        return Config.USER_ROLES.get(self.role, self.role)

    def can_manage_tournament(self, tournament_id=None):
        """Может ли управлять турниром"""
        return self.is_admin

    def can_judge_fights(self, fight=None):
        """Может ли судить схватки"""
        if not self.is_referee:
            return False

        if fight and self.tatami_assigned:
            return fight.tatami == self.tatami_assigned

        return True

    def get_assigned_fights(self, tournament_id=None):
        """Получить назначенные схватки"""
        from models.fight import Fight

        query = Fight.query

        if tournament_id:
            query = query.filter_by(tournament_id=tournament_id)

        if self.tatami_assigned:
            query = query.filter_by(tatami=self.tatami_assigned)

        return query.filter(Fight.status.in_(['SCHEDULED', 'LIVE'])).all()

    @classmethod
    def get_by_username(cls, username):
        """Получить пользователя по имени"""
        return cls.query.filter_by(username=username, is_active=True).first()

    @classmethod
    def get_referees(cls):
        """Получить всех судей"""
        return cls.query.filter_by(role='REFEREE', is_active=True).all()

    @classmethod
    def create_default_users(cls):
        """Создать пользователей по умолчанию"""
        users_data = [
            {'username': 'admin', 'password': 'admin', 'name': 'Администратор', 'role': 'ADMIN'},
            {'username': 'referee1', 'password': 'ref1', 'name': 'Судья 1', 'role': 'REFEREE', 'tatami_assigned': 1},
            {'username': 'referee2', 'password': 'ref2', 'name': 'Судья 2', 'role': 'REFEREE', 'tatami_assigned': 2},
            {'username': 'scoreboard', 'password': 'score', 'name': 'Оператор табло', 'role': 'SCOREBOARD'},
        ]

        for user_data in users_data:
            if not cls.get_by_username(user_data['username']):
                user = cls(
                    username=user_data['username'],
                    name=user_data['name'],
                    role=user_data['role']
                )
                if 'tatami_assigned' in user_data:
                    user.tatami_assigned = user_data['tatami_assigned']
                user.set_password(user_data['password'])
                db.session.add(user)

        db.session.commit()