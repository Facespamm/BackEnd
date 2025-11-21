from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

db = SQLAlchemy()

# Используйте одну строку подключения
DATABASE_URI = 'postgresql+psycopg2://postgres:password@localhost:5434/judo_tournament'

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if not database_exists(DATABASE_URI):
        create_database(DATABASE_URI)
        print("База данных создана!")

    db.init_app(app)
    with app.app_context():
        from models.athlete import Athlete
        from models.club import Club
        from models.tournament import Tournament
        from models.category import Category
        from models.fight import Fight
        from models.bracket import Bracket
        from models.result import Result
        from models.weighing import Weighing
        db.create_all()

def create_session():
    engine = create_engine(DATABASE_URI)
    session = sessionmaker(bind=engine)
    return session()  # Возвращайте экземпляр сессии