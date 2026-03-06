from sqlalchemy import delete

from database.db import get_session
from new_model.head_model.fight_new import FightNew
from new_model.head_model.new_athlete import AthleteNew
from new_model.head_model.new_user import UserNew
from new_model.new_associations import TournamentCategory
from new_model.result_new import ResultNew


class ResultRepository:
    def __init__(self, session=None):
        self.session = session if session else get_session()
        self._owns_session = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._owns_session:
            return
        if exc_type:
            self.session.rollback()
        self.session.close()

    def get_loser(self, fight_id):
        fight = (
            self.session.query(FightNew)
            .join(ResultNew, FightNew.id == ResultNew.fight_id)
            .filter(ResultNew.fight_id == fight_id)
            .one_or_none()
        )
        if not fight:
            return None
        result = self.session.query(ResultNew).filter(ResultNew.fight_id == fight_id).one_or_none()
        from repository.athlete_repo import AthleteRepository
        athlete_repo = AthleteRepository(self.session)
        if result.winner_id == fight.white_athlete_id:
            return athlete_repo.get_athlete_by_id(fight.blue_athlete_id)
        else:
            return athlete_repo.get_athlete_by_id(fight.white_athlete_id)

    def get_results_by_tournament(self, tournament_id, category_id):
        query = (
            self.session.query(ResultNew)
            .join(FightNew, ResultNew.fight_id == FightNew.id)
            .join(TournamentCategory, FightNew.tournament_category_id == TournamentCategory.tournament_category_id)
        )
        if tournament_id is not None and category_id is not None:
            query = query.filter(
                TournamentCategory.tournament_id == tournament_id,
                TournamentCategory.category_id == category_id
            )
        return query.all()

    def get_result_by_id(self, result_id):
        return self.session.query(ResultNew).filter_by(id=result_id).one_or_none()

    def get_result_by_fight(self, fight_id):
        return self.session.query(ResultNew).filter_by(fight_id=fight_id).first()

    def delete_result(self, fight_id):
        try:
            self.session.execute(delete(ResultNew).where(ResultNew.fight_id == fight_id))
            self.session.commit()
            return True
        except Exception as e:
            print("Error ", e)
            self.session.rollback()
            return False