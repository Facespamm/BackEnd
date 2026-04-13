import os
from contextlib import contextmanager

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

db = SQLAlchemy()

DATABASE_URI = 'postgresql+psycopg2://postgres:password@localhost:5434/judo_tournament'

_engine = None
_SessionFactory = None


def get_engine():
    global _engine
    if _engine is None:
        uri = os.getenv('LOCALHOST_CONNECTION', DATABASE_URI)
        _engine = create_engine(
            uri,
            pool_size=10,
            max_overflow=5,
            pool_timeout=30,
            pool_pre_ping=True,
            # echo = True
        )
    return _engine


def get_session_factory():
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine())
    return _SessionFactory


@contextmanager
def create_session():
    """Контекстный менеджер для роутов.

    Использование:
        with create_session() as session:
            repo = MyRepository(session)
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session():
    """Прямое получение сессии для репозиториев и init-скриптов.
    Вызывающий код сам отвечает за session.close().

    Использование:
        session = get_session()
        repo = MyRepository(session)
        ...
        session.close()
    """
    return get_session_factory()()


def init_db(app):
    uri = os.getenv('LOCALHOST_CONNECTION', DATABASE_URI)
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if not database_exists(uri):
        create_database(uri)
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
        from new_model.new_associations import TournamentCategory, AthleteRegistration, FightReferee
        from new_model.tatami_fight import TatamiFight
        from new_model.AthleteTournamentRegistration import AthleteTournamentRegistration
        db.create_all()