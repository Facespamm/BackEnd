import logger
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
log = logger.logger

def init_db(app):
    """Инициализация и создание таблиц"""
    db.init_app(app)
    
    with app.app_context():        # ← ЭТО ОБЯЗАТЕЛЬНО!
        log.info("Создаём таблицы в базе данных...")
        db.create_all()
        log.info("Таблицы успешно созданы (или уже существуют)")