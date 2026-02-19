from sqlalchemy import delete, true

from api.referee import delete_referee
from database.db import create_session
from new_model.head_model.fight_new import FightNew
from new_model.head_model.new_athlete import AthleteNew
from new_model.head_model.new_user import UserNew
from new_model.new_associations import TournamentCategory
from new_model.result_new import ResultNew
from repository.athlete_repo import AthleteRepository


class ResultRepository:
    def __init__(self):
        self.session = create_session()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        self.session.close()

    def get_loser(self,fight_id):
        fight = (
            self.session.query(FightNew)
            .join(ResultNew, FightNew.id == ResultNew.fight_id)
            .filter(
                ResultNew.fight_id == fight_id,
            )
            .one_or_none()
        )

        if not fight:
            return None

        result = self.session.query(ResultNew).filter(ResultNew.fight_id == fight_id).one_or_none()

        athlete_repo = AthleteRepository()
        if result.winner_id == fight.white_athlete_id:
            athlete = athlete_repo.get_athlete_by_id(fight.blue_athlete_id)
            return athlete #проигравший
        else:
            athlete = athlete_repo.get_athlete_by_id(fight.white_athlete_id)
            return athlete # проигравший

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

    def get_result_by_fight(self, fight_id):
        return self.session.query(ResultNew).filter_by(fight_id=fight_id).one_or_none()

    def delete_result(self, fight_id):
        try:
            delete_query = (
                delete(ResultNew)
                .where(ResultNew.fight_id == fight_id)
            )

            self.session.execute(delete_query)
            self.session.commit()
            self.session.close()
            return True
        except Exception as e:
            print("Error ", e)
            self.session.rollback()
            self.session.close()
            return False