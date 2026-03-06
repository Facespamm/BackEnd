from database.db import get_session
from new_model.handbook.new_dan import DanNew
from new_model.head_model.new_athlete import AthleteNew


class DanRepository:
    def __init__(self, session=None):
        self.session = session if session else get_session()
        self._owns_session = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._owns_session:
            return
        if exc_type is not None:
            self.session.rollback()
        self.session.close()

    def get_dans(self):
        try:
            return self.session.query(DanNew).all()
        except Exception as e:
            print("❌ Exception: ", e)
            return []

    def get_athletes_count(self, dan_id):
        try:
            return self.session.query(AthleteNew).filter(AthleteNew.rank_id == dan_id).count()
        except Exception as e:
            print(f"Error getting athletes count: {e}")
            return 0

    def get_dan_by_name(self, level: str):
        try:
            return self.session.query(DanNew).filter(DanNew.level == level).one_or_none()
        except Exception as e:
            print(f"Error getting dan by name: {e}")
            return None

    def create_dan(self, dan: DanNew):
        try:
            self.session.add(dan)
            self.session.commit()
            return dan.id
        except Exception as e:
            self.session.rollback()
            print(f"Error creating dan: {e}")
            return None