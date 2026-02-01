from database.db import create_session


class ScoreEvenRepository:
    def __init__(self):
        self.session = create_session()

    def create_score_event(self, score_event):
        try:
            self.session.add(score_event)
            self.session.commit()
            return score_event.id
        except Exception as e:
            self.session.rollback()
            print('Error: ', e)
            return None