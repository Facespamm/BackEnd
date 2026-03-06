from database.db import get_session
from new_model.Enums import EventType
from new_model.score_event import ScoreEvent


class ScoreEvenRepository:
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

    def create_score_event(self, score_event: ScoreEvent):
        try:
            self.session.add(score_event)
            self.session.commit()
            return score_event.id
        except Exception as e:
            self.session.rollback()
            print('Error: ', e)
            return None

    def get_score_events(self, fight_id, athlete_id, event_type=None, score_type=None):
        try:
            query = self.session.query(ScoreEvent).filter_by(fight_id=fight_id, athlete_id=athlete_id)
            if event_type:
                query = query.filter_by(event_type=event_type)
            if score_type:
                query = query.filter_by(score_type=score_type)
            return query.all()
        except Exception as e:
            print('Error: ', e)
            return None

    def get_oseakomi_events(self, fight_id, athlete_id):
        try:
            return (
                self.session.query(ScoreEvent)
                .filter_by(fight_id=fight_id, athlete_id=athlete_id, event_type=EventType.OSAEKOMI_START)
                .order_by(ScoreEvent.created_at.desc())
                .one()
            )
        except Exception as e:
            print('Error: ', e)
            return None