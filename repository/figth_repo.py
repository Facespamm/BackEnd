from datetime import timedelta

from sqlalchemy import delete, insert, select, update

from database.db import get_session
from models.Enums import BracketType, FightStatus, TatamiStatus, text_to_fight_status
from models.fight_new import FightNew
from models.new_associations import FightReferee, TournamentCategory
from models.new_referee import RefereeNew
from models.result_new import ResultNew
from models.tatami_fight import TatamiFight


class FightRepository:
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

    def assign_referee(self, referee_id, fight_id, role):
        existing = self.session.execute(
            select(FightReferee)
            .where(FightReferee.fight_id == fight_id)
            .where(FightReferee.role == role)
        ).first()

        if existing:
            self.session.execute(
                update(FightReferee)
                .where(FightReferee.fight_id == fight_id)
                .where(FightReferee.role == role)
                .values(referee_id=referee_id)
            )
        else:
            self.session.execute(
                insert(FightReferee).values(
                    fight_id=fight_id, referee_id=referee_id, role=role
                )
            )
        self.session.commit()

    def get_fights_by_bracket_type(
        self, tournament_category_id, bracket_type: BracketType
    ):
        return (
            self.session.query(FightNew)
            .filter(
                FightNew.tournament_category_id == tournament_category_id,
                FightNew.type_bracket == bracket_type,
            )
            .order_by(FightNew.round_number, FightNew.fight_number)
            .all()
        )

    def remove_referee(self, fight_id, role):
        self.session.execute(
            delete(FightReferee)
            .where(FightReferee.fight_id == fight_id)
            .where(FightReferee.role == role)
        )
        self.session.commit()

    def create_fight(self, fight):
        try:
            self.session.add(fight)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print("Error: ", e)
            raise e

    def get_fight_by_tournament(
        self,
        tournament_category_id,
        status: FightStatus = None,
        minimal_round_number=None,
    ):
        query = self.session.query(FightNew).filter_by(
            tournament_category_id=tournament_category_id
        )
        if status:
            query = query.filter_by(status=status)

        if minimal_round_number:
            query = query.filter_by(round_number=minimal_round_number)
        return query.all()

    def get_fights_by_search_params(
        self, tournament_id=None, tatami_number=None, status=None
    ):
        query = self.session.query(FightNew)
        if tournament_id:
            query = query.join(
                TournamentCategory, TournamentCategory.tournament_id == tournament_id
            )
        if status:
            status_in_enum = text_to_fight_status(status)
            query = query.filter(FightNew.status == status_in_enum.name)
        if tatami_number:
            query = query.filter(FightNew.tatami_number == tatami_number)
        return query.order_by(FightNew.tatami_number, FightNew.created_at).all()

    def get_fight_by_id(self, fight_id):
        return self.session.query(FightNew).filter_by(id=fight_id).first()

    def get_fight_referees(self, fight_id):
        fight_referees = (
            self.session.query(
                RefereeNew.first_name,
                RefereeNew.last_name,
                RefereeNew.middle_name,
                FightReferee.role,
            )
            .join(FightReferee, FightReferee.referee_id == RefereeNew.id)
            .filter(FightReferee.fight_id == fight_id)
            .all()
        )
        return [
            {
                "first_name": r.first_name,
                "last_name": r.last_name,
                "middle_name": r.middle_name,
                "role": r.role,
            }
            for r in fight_referees
        ]

    def set_live_status(self, fight_id, tatami_number):
        try:
            fight = self.get_fight_by_id(fight_id)
            if fight:
                fight.status = FightStatus.LIVE
                fight.tatami_number = tatami_number
                fight.start_time = timedelta(minutes=0, seconds=0)

                tournament_id = (
                    self.session.query(TournamentCategory.tournament_id)
                    .filter(
                        TournamentCategory.tournament_category_id
                        == fight.tournament_category_id
                    )
                    .distinct(TournamentCategory.tournament_id)
                    .scalar()
                )

                if tournament_id:
                    tatami_fight = (
                        self.session.query(TatamiFight)
                        .filter_by(
                            tournament_id=tournament_id, tatami_number=tatami_number
                        )
                        .first()
                    )
                    if tatami_fight:
                        tatami_fight.fight_id = fight.id
                        tatami_fight.status = TatamiStatus.TAKEN
                    else:
                        self.session.add(
                            TatamiFight(
                                tournament_id=tournament_id,
                                tatami_number=tatami_number,
                                fight_id=fight.id,
                                status=TatamiStatus.TAKEN,
                            )
                        )
            self.session.commit()
        except Exception as e:
            print("Error: ", e)
            self.session.rollback()
            raise e

    def update_fight(self, fight_id, next_fight_id):
        try:
            current_fight = self.get_fight_by_id(fight_id)
            next_fight = self.get_fight_by_id(next_fight_id)
            current_fight.next_fight_id = next_fight_id

            if current_fight.round_number == 1:
                if current_fight.white_athlete_id and not current_fight.blue_athlete_id:
                    if not next_fight.white_athlete_id:
                        next_fight.white_athlete_id = current_fight.white_athlete_id
                    elif not next_fight.blue_athlete_id:
                        next_fight.blue_athlete_id = current_fight.white_athlete_id
                    current_fight.status = FightStatus.COMPLETED
                elif (
                    current_fight.blue_athlete_id and not current_fight.white_athlete_id
                ):
                    if not next_fight.white_athlete_id:
                        next_fight.white_athlete_id = current_fight.blue_athlete_id
                    elif not next_fight.blue_athlete_id:
                        next_fight.blue_athlete_id = current_fight.blue_athlete_id
                    current_fight.status = FightStatus.COMPLETED
            self.session.commit()
        except Exception as e:
            print("Error: ", e)
            self.session.rollback()
            raise e

    def get_all_fights_by_tournament_category(self, tournament_category_id: int):
        return (
            self.session.query(FightNew)
            .filter(FightNew.tournament_category_id == tournament_category_id)
            .order_by(FightNew.round_number, FightNew.fight_number)
            .all()
        )

    def end_fight(self, fight_id, data: dict):
        try:
            fight = self.get_fight_by_id(fight_id)
            end_time = self._text_to_time(data["end_time"])
            fight.end_time = end_time
            fight.status = FightStatus.COMPLETED

            taken_tatami_fight = (
                self.session.query(TatamiFight).filter_by(fight_id=fight.id).first()
            )
            if not taken_tatami_fight:
                raise Exception("Tatami fight not found")
            taken_tatami_fight.fight_id = None
            taken_tatami_fight.status = TatamiStatus.FREE

            fight_duration = end_time - fight.start_time
            athlete_id = int(data.get("winner_athlete_id"))
            new_result = ResultNew(
                fight_id=fight_id,
                winner_id=athlete_id,
                victory_type=data.get("victory_type"),
                fight_duration=int(fight_duration.total_seconds()),
                count_of_fights_win=1,
            )
            self.move_athlete_next_fight(fight_id, athlete_id)
            self.session.add(new_result)
            self.session.commit()
        except Exception as e:
            print("Error: ", e)
            self.session.rollback()
            raise e

    def move_athlete_next_fight(self, fight_id, athlete_id):
        try:
            fight = self.get_fight_by_id(fight_id)
            if not fight.next_fight_id:
                return
            next_fight = self.get_fight_by_id(fight.next_fight_id)
            if not fight or not next_fight:
                raise Exception("Fight or next fight not found")

            if fight.blue_athlete_id == athlete_id and not next_fight.white_athlete_id:
                next_fight.white_athlete_id = athlete_id
            elif (
                fight.white_athlete_id == athlete_id and not next_fight.blue_athlete_id
            ):
                next_fight.blue_athlete_id = athlete_id
            elif not next_fight.white_athlete_id:
                next_fight.white_athlete_id = athlete_id
            elif not next_fight.blue_athlete_id:
                next_fight.blue_athlete_id = athlete_id
            else:
                print("Error: Athlete not found in the fight")
                return
            self.session.commit()
        except Exception as e:
            print("Error: ", e)
            self.session.rollback()
            raise e

    def get_semi_final_fights(
        self, tournament_category_id, semi_final_round_number, eight_round=1
    ):
        return (
            self.session.query(FightNew)
            .filter(
                FightNew.tournament_category_id == tournament_category_id,
                FightNew.round_number <= semi_final_round_number,
                FightNew.round_number >= eight_round,
            )
            .all()
        )

    def get_untracked_semifinal_fights(
        self, tournament_category_id, semi_final_round_number, eight_round
    ):
        fights = (
            self.session.query(FightNew)
            .filter(
                FightNew.tournament_category_id == tournament_category_id,
                FightNew.round_number <= semi_final_round_number,
                FightNew.round_number >= eight_round,
                FightNew.type_bracket == BracketType.MAIN,
            )
            .all()
        )
        self.session.expunge_all()
        return fights

    def get_final_fights(self, tournament_category_id, final_round_number):
        return (
            self.session.query(FightNew)
            .filter(
                FightNew.tournament_category_id == tournament_category_id,
                FightNew.round_number == final_round_number,
            )
            .all()
        )

    def _text_to_time(self, text):
        try:
            m, s = map(int, text.split(":"))
            return timedelta(minutes=m, seconds=s)
        except Exception as e:
            print("Error: ", e)
            return None

    def create_result(self, result):
        try:
            self.session.add(result)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print("Error: ", e)
            raise e

    def update_end_time(self, fight_id, end_time: timedelta):
        try:
            fight = self.get_fight_by_id(fight_id)
            if fight:
                fight.end_time = end_time
                self.session.commit()
        except Exception as e:
            print("Error: ", e)
            self.session.rollback()

    def tatami_is_taken(self, fight_id, tatami_number):
        fight = self.get_fight_by_id(fight_id)
        tournament_id = (
            self.session.query(TournamentCategory.tournament_id)
            .filter(
                TournamentCategory.tournament_category_id
                == fight.tournament_category_id
            )
            .distinct(TournamentCategory.tournament_id)
            .scalar()
        )
        tatami_fight = (
            self.session.query(TatamiFight)
            .filter_by(tournament_id=tournament_id, tatami_number=tatami_number)
            .scalar()
        )
        return bool(tatami_fight and tatami_fight.status == TatamiStatus.TAKEN)

    def remove_winner_from_next_fight(self, next_fight_id, winner_id):
        try:
            next_fight = self.get_fight_by_id(next_fight_id)
            if next_fight and next_fight.blue_athlete_id == winner_id:
                next_fight.blue_athlete_id = None
            elif next_fight and next_fight.white_athlete_id == winner_id:
                next_fight.white_athlete_id = None
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def flush_create(self, fight):
        try:
            self.session.add(fight)
            self.session.flush()
        except Exception as e:
            print("Error: ", e)
            self.session.rollback()

    def update_status(self, fight_id, status):
        try:
            fight = self.get_fight_by_id(fight_id)
            if fight:
                fight.status = status
                self.session.commit()
        except Exception as e:
            print("Error: ", e)
            self.session.rollback()
            raise e

    def update_athlete_in_next_rounds(self, fight, old_athlete_id, new_athlete_id):
        """Рекурсивно обновляет атлета в следующих раундах"""
        if not fight.next_fight_id:
            return

        next_fight = self.get_fight_by_id(fight.next_fight_id)
        if not next_fight:
            return

        if next_fight.blue_athlete_id == old_athlete_id:
            next_fight.blue_athlete_id = new_athlete_id
            self.update_athlete_in_next_rounds(
                next_fight, old_athlete_id, new_athlete_id
            )
        elif next_fight.white_athlete_id == old_athlete_id:
            next_fight.white_athlete_id = new_athlete_id
            self.update_athlete_in_next_rounds(
                next_fight, old_athlete_id, new_athlete_id
            )

    def change_tamami(self, fight_id, tatami_number):
        try:
            fight = self.get_fight_by_id(fight_id)
            if fight is None:
                raise ValueError(f"Бой с id={fight_id} не найден")
            fight.tatami_number = tatami_number
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
