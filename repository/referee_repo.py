from database.db import create_session
from new_model.handbook.new_referee import RefereeNew


class RefereeRepository:
    def __init__(self):
        self.session = create_session()

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
            referee.phone = data.get('name', referee.phone)
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
            return False