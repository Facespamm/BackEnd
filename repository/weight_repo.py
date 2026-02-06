from database.db import create_session
from new_model.weighing_new import WeighingNew


class WeightRepository:
    def __init__(self):
        self.session = create_session()

    def get_weights(self, tournament_category_id: int, athlete_id:int) -> list[WeighingNew] | None:
        try:
            query = self.session.query(WeighingNew).filter_by(tournament_category_id=tournament_category_id)

            if athlete_id:
                query = query.filter_by(athlete_id=athlete_id)

            weighings = query.order_by(WeighingNew.weighing_time.desc()).all()
            return weighings
        except Exception as e:
            print('Error ',e)
            return None

    def get_weight(self, weighing_id:int) -> WeighingNew | None:
        try:
            weight = self.session.query(WeighingNew).filter_by(weighing_id=weighing_id).first()
            return weight
        except Exception as e:
            print('Error ',e)
            return None

    def change_weighing_validation(self, weighing_id:int):
        try:
            weight = self.get_weight(weighing_id)

            if not weight:
                return False

            weight.is_valid = not weight.is_valid
            self.session.commit()
            return True
        except Exception as e:
            print('Error ',e)
            self.session.rollback()
            return False

    def update_weighing_information(self, weight_id:int, data:dict) -> bool:
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
            print('Error ',e)
            self.session.rollback()
            return False

    def create_weighting(self, weight:WeighingNew):
        try:
            self.session.add(weight)
            self.session.commit()
            return True
        except Exception as e:
            print('Error ',e)
            self.session.rollback()
            return False