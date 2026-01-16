from database.db import create_session
from new_model.result_new import ResultNew


class ResultRepository:
    def __init__(self):
        self.session = create_session()

    def get_loser(self,fight_id):
        return self.session.query(ResultNew).filter_by(fight_id=fight_id).one_or_none()