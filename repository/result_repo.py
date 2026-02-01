from database.db import create_session
from new_model.head_model.fight_new import FightNew
from new_model.head_model.new_athlete import AthleteNew
from new_model.head_model.new_user import UserNew
from new_model.new_associations import TournamentCategory
from new_model.result_new import ResultNew


class ResultRepository:
    def __init__(self):
        self.session = create_session()

    def get_loser(self,fight_id):
        return self.session.query(ResultNew).filter_by(fight_id=fight_id).one_or_none()

    def get_results_by_tournament(self, tournament_id, category_id):
        results = (
            self.session.query(ResultNew)
            .join(FightNew, ResultNew.fight_id == FightNew.id)
            .join(TournamentCategory, FightNew.tournament_category_id == TournamentCategory.tournament_category_id)
        )

        if tournament_id is not None and category_id is not None:
            results = results.filter(
                TournamentCategory.tournament_id == tournament_id,
                TournamentCategory.category_id == category_id
            )

        return results.all()

    def get_result_by_id(self, result_id):
        return self.session.query(ResultNew).filter_by(id=result_id).one_or_none()

