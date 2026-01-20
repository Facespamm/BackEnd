from sqlalchemy import select
from sqlalchemy.sql.functions import count

from database.db import create_session
from new_model.handbook.new_dan import DanNew
from new_model.head_model.new_athlete import AthleteNew


class DanRepository:
    def __init__(self):
        self.session = create_session()

    def get_dans(self):
        try:
            dans_query = (
                select(DanNew.id, DanNew.level, DanNew.description, count(AthleteNew.id).label('athlete_count'))
                .join(AthleteNew, DanNew.id == AthleteNew.dan_id)
            )

            dans = self.session.execute(dans_query).all()
            return dans
        except Exception as e:
            print("❌ Exception: ", e)
            return []

    def get_dan_by_name(self, level: str):
        """Получить дан по его уровню"""
        try:
            dan = self.session.query(DanNew).filter_by(level == level).one_or_none()
            return dan
        except Exception as e:
            print(f"Error getting dan by name: {e}")
            return None

    def create_dan(self, dan:DanNew):
        """Создать новый дан"""
        try:
            self.session.add(dan)
            self.session.commit()
            return dan.id
        except Exception as e:
            self.session.rollback()
            print(f"Error creating dan: {e}")
            return None