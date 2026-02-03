from database.db import create_session
from new_model.Enums import EventType
from new_model.score_event import ScoreEvent


class ScoreEvenRepository:
    def __init__(self):
        self.session = create_session()

    def create_score_event(self, score_event:ScoreEvent):
        try:
            self.session.add(score_event)
            self.session.commit()
            return score_event.id
        except Exception as e:
            self.session.rollback()
            print('Error: ', e)
            return None

    def get_score_events(self, fight_id, athlete_id, EventType=None, ScoreType=None):
        try:
            event_query = self.session.query(ScoreEvent).filter_by(fight_id=fight_id, athlete_id=athlete_id)

            if EventType:
                event_query = event_query.filter_by(event_type=EventType)

            if ScoreType:
                event_query = event_query.filter_by(score_type=ScoreType)

            return event_query.all()
        except Exception as e:
            print('Error: ', e)
            return None

    def get_oseakomi_events(self,  fight_id, athlete_id):
        try:
            event_query = self.session.query(ScoreEvent).filter_by(
                fight_id=fight_id,
                athlete_id=athlete_id,
                event_type=EventType.OSAEKOMI_START
            ).order_by(ScoreEvent.created_at.desc())

            return event_query.one()
        except Exception as e:
            print('Error: ', e)
            return None