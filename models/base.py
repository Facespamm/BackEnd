from datetime import datetime
from database.db import db

class BaseModel(db.Model):
    """
    Базовая модель с общими полями
    """
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def save(self):
        """
        Сохранить объект в базу данных
        """
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка сохранения: {e}")
            return False

    def delete(self):
        """
        Удалить объект из базы данных
        """
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка удаления: {e}")
            return False

    def to_dict(self):
        """
        Преобразовать объект в словарь
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    @classmethod
    def get_by_id(cls, id):
        """
        Получить объект по ID
        """
        return cls.query.get(id)

    @classmethod
    def get_all(cls):
        """
        Получить все объекты
        """
        return cls.query.all()