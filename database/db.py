import os

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy_utils import database_exists, create_database

db = SQLAlchemy()

# Используйте одну строку подключения
# DATABASE_URI = 'postgresql+psycopg2://postgres:password@192.168.7.122:5434/judo_tournament'
DATABASE_URI = 'postgresql+psycopg2://postgres:password@localhost:5434/judo_tournament'
#docker connection
# DATABASE_URI = 'postgresql+psycopg2://postgres:password@db:5432/judo_tournament'

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('LOCALHOST_CONNECTION',DATABASE_URI)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if not database_exists(os.getenv('LOCALHOST_CONNECTION',DATABASE_URI)):
        create_database(os.getenv('LOCALHOST_CONNECTION',DATABASE_URI))
        print("База данных создана!")

    db.init_app(app)
    with app.app_context():
        from new_model.handbook.new_club import ClubNew
        from new_model.handbook.new_dan import DanNew
        from new_model.handbook.new_referee import RefereeNew
        from new_model.head_model.tournament_new import TournamentNew
        from new_model.handbook.category_new import CategoryNew
        from new_model.handbook.role_new import RoleNew
        from new_model.head_model.new_user import UserNew
        from new_model.head_model.fight_new import FightNew
        from new_model.head_model.new_athlete import AthleteNew
        from new_model.result_new import ResultNew
        from new_model.score_event import ScoreEvent
        from new_model.weighing_new import WeighingNew
        from new_model.new_associations import TournamentCategory, AthleteRegistration,FightReferee
        from new_model.tatami_fight import TatamiFight
        db.create_all()

def create_session():
    engine = create_engine(os.getenv('LOCALHOST_CONNECTION',DATABASE_URI))
    session = sessionmaker(bind=engine)
    return  scoped_session(session)  # Возвращайте экземпляр сессии