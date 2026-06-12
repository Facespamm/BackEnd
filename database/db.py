import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


_engine = None
_SessionFactory = None


def get_engine():
    global _engine
    if _engine is None:
        uri = os.getenv(
            "LOCALHOST_CONNECTION",
            "postgresql+psycopg2://postgres:password@localhost:5434/judo_tournament",
        )
        if not uri:
            raise ValueError("DATABASE_URL environment variable is not set")
        _engine = create_engine(
            uri,
            pool_size=10,
            max_overflow=5,
            pool_timeout=30,
            pool_pre_ping=True,
            # echo=True,
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


def init_db():
    uri = os.getenv(
        "LOCALHOST_CONNECTION",
        "postgresql+psycopg2://postgres:password@localhost:5434/judo_tournament",
    )

    from sqlalchemy_utils import create_database, database_exists

    if not database_exists(uri):
        create_database(uri)
        print("База данных создана!")

    import models

    Base.metadata.create_all(bind=get_engine())
    print("База данных и таблицы созданы!")
