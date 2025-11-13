from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def init_db(app):
    """
    Инициализация базы данных
    """
    db.init_app(app)

    with app.app_context():
        try:
            # Импорт всех моделей для создания таблиц
            from models.athlete import Athlete
            from models.club import Club
            from models.tournament import Tournament
            from models.category import Category
            from models.fight import Fight
            from models.bracket import Bracket
            from models.result import Result
            from models.user import User
            from models.weighing import Weighing

            # Создание всех таблиц
            db.create_all()
            print("✅ База данных инициализирована")

            # Создание тестового администратора если нет пользователей
            if User.query.count() == 0:
                from utils.security import hash_password
                admin = User(
                    username='admin',
                    password_hash=hash_password('admin'),
                    role='ADMIN',
                    name='Администратор'
                )
                db.session.add(admin)
                db.session.commit()
                print("👤 Создан тестовый администратор (admin/admin)")

        except Exception as e:
            print(f"❌ Ошибка инициализации БД: {e}")
            db.session.rollback()