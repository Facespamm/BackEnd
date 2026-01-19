from database.db import create_session
from new_model.handbook.new_dan import DanNew
from new_model.head_model.new_athlete import AthleteNew


class DanRepository:
    def __init__(self):
        self.session = create_session()

    #TODO доделать методы репозитория для дана
    def get_dans(self):
        try:
            dans_query = (
                select(DanNew)
            )
            return dans
        except Exception as e:
            print("❌ Exception: ", e)
            return []
