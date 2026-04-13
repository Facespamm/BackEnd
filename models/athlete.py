from datetime import datetime
from database.db import db
# from models.fight import Fight

#TODO возможно пренисти некоторые методы  в repository
# class Athlete:
#     """
#     Модель участника турнира
#     """
#     __tablename__ = 'athletes'
#
#     # Основная информация
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
#     birth_date = db.Column(db.Date, nullable=False)
#     gender = db.Column(db.String(10), nullable=False)
#     club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'))
#     rank_id = db.Column(db.Integer, db.ForeignKey('dans.id'))  # КЮ/ДАН
#     license_number = db.Column(db.String(50))
#     medical_check = db.Column(db.Boolean, default=False)
#     insurance_number = db.Column(db.String(50))
#     is_active = db.Column(db.Boolean, default=True)
#
#     # Связи
#     user = db.relationship('User', back_populates='athlete_profile', uselist=False)
#     club = db.relationship('Club', backref=db.backref('athletes', lazy=True))
#     weighings = db.relationship('Weighing', back_populates='athlete', lazy=True)
#     rank = db.relationship('Dan', back_populates='athletes')
#
#     fights_as_white = db.relationship('Fight',
#                                       foreign_keys='Fight.white_athlete_id',
#                                       back_populates='white_athlete')
#     fights_as_blue = db.relationship('Fight',
#                                      foreign_keys='Fight.blue_athlete_id',
#                                      back_populates='blue_athlete')
#
#     # Свойства для доступа к данным пользователя
#     @property
#     def first_name(self):
#         """Имя участника (из связанного пользователя)"""
#         return self.user.first_name if self.user else None
#
#     @property
#     def last_name(self):
#         """Фамилия участника (из связанного пользователя)"""
#         return self.user.last_name if self.user else None
#
#     @property
#     def middle_name(self):
#         """Отчество участника (из связанного пользователя)"""
#         return self.user.middle_name if self.user else None
#
#     def __repr__(self):
#         """Безопасное строковое представление"""
#         if self.user:
#             return f'<Athlete {self.last_name} {self.first_name}>'
#         return f'<Athlete id:{self.id}>'
#
#     @property
#     def full_name(self):
#         """Полное имя участника"""
#         if not self.user:
#             return "Неизвестный участник"
#
#         parts = []
#         if self.last_name:
#             parts.append(self.last_name)
#         if self.first_name:
#             parts.append(self.first_name)
#         if self.middle_name:
#             parts.append(self.middle_name)
#
#         return " ".join(parts) if parts else "Без имени"
#
#     @property
#     def age(self):
#         """Возраст участника"""
#         if not self.birth_date:
#             return None
#
#         today = datetime.today()
#         return today.year - self.birth_date.year - (
#                 (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
#         )
#
#     def get_current_weight(self, tournament_id=None):
#         """Получить текущий вес участника"""
#         from models.weighing import Weighing
#         weighing = Weighing.query.filter_by(
#             athlete_id=self.id,
#             tournament_id=tournament_id
#         ).order_by(Weighing.created_at.desc()).first()
#         return weighing.weight if weighing else None
#
#     def get_fights_count(self, tournament_id=None):
#         """Получить количество схваток"""
#         query = Fight.query.filter(
#             (Fight.white_athlete_id == self.id) | (Fight.blue_athlete_id == self.id)
#         )
#         if tournament_id:
#             query = query.filter_by(tournament_id=tournament_id)
#         return query.count()
#
#     def get_victories_count(self, tournament_id=None):
#         """Получить количество побед"""
#         from models.result import Result
#         query = Result.query.filter_by(winner_id=self.id)
#         if tournament_id:
#             query = query.join(Fight).filter(Fight.tournament_id == tournament_id)
#         return query.count()
#
#     def save_to_db(self):
#         try:
#             db.session.add(self)
#             db.session.commit()
#             return True
#         except Exception as e:
#             db.session.rollback()
#             print(f"Error saving Athlete to DB: {e}")
#             return False