from database.db import get_session
from new_model.weighing_new import WeighingNew


class WeightRepository:
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

    def get_weights(self, tournament_category_id: int, athlete_id: int) -> list[WeighingNew] | None:
        try:
            query = self.session.query(WeighingNew).filter_by(tournament_category_id=tournament_category_id)
            if athlete_id:
                query = query.filter_by(athlete_id=athlete_id)
            return query.order_by(WeighingNew.weighing_time.desc()).all()
        except Exception as e:
            print('Error ', e)
            return None

    def get_weight(self, weighing_id: int) -> WeighingNew | None:
        try:
            return self.session.query(WeighingNew).filter_by(id=weighing_id).first()
        except Exception as e:
            print('Error ', e)
            return None

    def change_weighing_validation(self, weighing_id: int):
        try:
            weight = self.get_weight(weighing_id)
            if not weight:
                return False
            weight.is_valid = not weight.is_valid
            self.session.commit()
            return True
        except Exception as e:
            print('Error ', e)
            self.session.rollback()
            return False

    def update_weighing_information(self, weight_id: int, data: dict) -> bool:
        try:
            weighing = self.get_weight(weight_id)
            if 'weight' in data:
                weighing.weight = data['weight']
            if 'weight_category' in data:
                weighing.weight_category = data['weight_category']
            if 'is_valid' in data:
                weighing.is_valid = data['is_valid']
            if 'notes' in data:
                weighing.notes = data['notes']
            self.session.commit()
            return True
        except Exception as e:
            print('Error ', e)
            self.session.rollback()
            return False

    def create_weighting(self, weight: WeighingNew):
        try:
            self.session.add(weight)
            self.session.commit()
            return True
        except Exception as e:
            print('Error ', e)
            self.session.rollback()
            return False