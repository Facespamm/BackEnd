from database.db import get_session
from new_model.handbook.new_referee import RefereeNew
from new_model.new_associations import FightReferee


class RefereeRepository:
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

    def get_referees(self):
        return self.session.query(RefereeNew).all()

    def get_referee(self, referee_id):
        return self.session.query(RefereeNew).filter_by(id=referee_id).first()

    def create_referee(self, referee):
        try:
            self.session.add(referee)
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error: {e}")
            self.session.rollback()
            return False

    def update_referee(self, referee, data):
        try:
            referee.email = data.get('email', referee.email)
            referee.phone = data.get('phone', referee.phone)
            referee.certification_level = data.get('certification_level', referee.certification_level)
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error: {e}")
            self.session.rollback()
            return False

    def delete_referee(self, referee_id):
        try:
            existing_referee = self.get_referee(referee_id)
            self.session.delete(existing_referee)
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error: {e}")
            self.session.rollback()
            return False

    def has_assign_referee(self, role, fight_id):
        existing = (
            self.session.query(RefereeNew)
            .join(FightReferee, FightReferee.referee_id == RefereeNew.id)
            .filter(FightReferee.fight_id == fight_id, FightReferee.role == role)
            .first()
        )
        return existing is not None