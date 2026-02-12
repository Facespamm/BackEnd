from datetime import timedelta

from sqlalchemy import select, update, insert, delete

from database.db import create_session
from new_model.Enums import text_to_fight_status, FightStatus, TatamiStatus
from new_model.handbook.new_referee import RefereeNew
from new_model.head_model.fight_new import FightNew
from new_model.new_associations import FightReferee, TournamentCategory
from new_model.result_new import ResultNew
from new_model.tatami_fight import TatamiFight

class FightRepository:
    def __init__(self):
        self.session = create_session()

    def assign_referee(self, referee_id, fight_id ,role):
        """Назначить судью на бой"""
        # Проверяем, не назначен ли уже судья на эту роль
        existing_query = (
            select(FightReferee)
            .where(FightReferee.fight_id == fight_id)
            .where(FightReferee.role == role)
        )
        existing = self.session.execute(existing_query).first()

        if existing:
            # Обновляем существующую запись
            update_query = (
                update(FightReferee)
                .where(FightReferee.fight_id == fight_id)
                .where(FightReferee.role == role)
                .values(referee_id=referee_id)
            )
            self.session.execute(update_query)
        else:
            # Добавляем новую запись
            insert_query = (
                insert(FightReferee)
                .values(
                    fight_id=fight_id,
                    referee_id=referee_id,
                    role=role
                )
            )
            self.session.execute(insert_query)
        self.session.commit()

    def remove_referee(self, fight_id,role):
        """Убрать судью с определенной роли"""
        delete_query = (
            delete(FightReferee)
            .where(FightReferee.fight_id == fight_id)
            .where(FightReferee.role == role)
        )
        self.session.execute(delete_query)
        self.session.commit()

    def create_fight(self, fight):
        try:
            self.session.add(fight)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print('Error: ',e)

    def get_fight_by_tournament(self, tournament_category_id, status : FightStatus = None):
        fights_query = self.session.query(FightNew).filter_by(tournament_category_id = tournament_category_id)

        if status:
            fights_query = fights_query.filter_by(status =status)

        return fights_query.all()

    def get_fights_by_search_params(self, tournament_id=None, tatami_number=None, status=None):
        select_query = self.session.query(FightNew)

        if tournament_id:
            select_query = select_query.join(TournamentCategory, TournamentCategory.tournament_id == tournament_id)

        if status:
            status_in_enum = text_to_fight_status(status)
            select_query = select_query.filter(FightNew.status == status_in_enum.name)

        if tatami_number:
            select_query = select_query.filter(FightNew.tatami_number == tatami_number)

        return  select_query.order_by(FightNew.tatami_number, FightNew.created_at).all()

    def get_fight_by_id(self, fight_id):
        return self.session.query(FightNew).filter_by(id=fight_id).first()

    def get_fight_referees(self, fight_id):
        fight_referees = (
            self.session.query(RefereeNew.first_name,RefereeNew.last_name, RefereeNew.middle_name,FightReferee.role)
            .join(FightReferee, FightReferee.referee_id == RefereeNew.id)
            .filter(
                FightReferee.fight_id == fight_id
            ).all()
        )

        referee_list = [{
            'first_name': referee.first_name,
            'last_name': referee.last_name,
            'middle_name': referee.middle_name,
            'role': referee.role
        } for referee in fight_referees]

        return referee_list

    def set_live_status(self, fight_id, tatami_number):
        try:
            fight = self.get_fight_by_id(fight_id)
            if fight:
                fight.status = FightStatus.LIVE
                fight.tatami_number = tatami_number
                fight.start_time = timedelta(minutes=0, seconds=0)

                tournament_id = (
                    self.session.query(TournamentCategory.tournament_id)
                    .filter(TournamentCategory.tournament_category_id == fight.tournament_category_id)
                    .distinct(TournamentCategory.tournament_id)
                    .first()
                )

                if tournament_id:
                    update_tatami_fight = (
                        update(TatamiFight)
                        .filter_by(tournament_id=tournament_id,tatami_number=tatami_number)
                        .values(fight_id=fight.id, status=TatamiStatus.TAKEN)
                    )
                    self.session.execute(update_tatami_fight)

            self.session.commit()
        except Exception as e:
            print('Error: ',e)
            self.session.rollback()

    def update_fight(self, fight_id,  next_fight_id):
        try:
            current_fight = self.get_fight_by_id(fight_id)
            next_fight = self.get_fight_by_id(next_fight_id)

            current_fight.next_fight_id = next_fight_id

            # Только белый атлет в текущем бою (белого нет - walkover)
            if current_fight.white_athlete_id and not current_fight.blue_athlete_id:
                if not next_fight.white_athlete_id:
                    next_fight.white_athlete_id = current_fight.white_athlete_id
                elif not next_fight.blue_athlete_id:
                    next_fight.blue_athlete_id = current_fight.white_athlete_id
                current_fight.status = FightStatus.COMPLETED

            # Только синий атлет в текущем бою (белого нет - walkover)
            elif current_fight.blue_athlete_id and not current_fight.white_athlete_id:
                if not next_fight.white_athlete_id:
                    next_fight.white_athlete_id = current_fight.blue_athlete_id
                elif not next_fight.blue_athlete_id:
                    next_fight.blue_athlete_id = current_fight.blue_athlete_id
                current_fight.status = FightStatus.COMPLETED

            self.session.commit()
        except Exception as e:
            print('Error: ', e)
            self.session.rollback()

    def end_fight(self, fight_id, data: dict):
        try:
            fight = self.get_fight_by_id(fight_id)

            start_time = fight.start_time
            end_time = self._text_to_time(data['end_time'])

            fight.end_time = end_time
            fight.status = FightStatus.COMPLETED

            taken_tatami_fight = self.session.query(TatamiFight).filter_by(fight_id=fight.id).first()

            if not taken_tatami_fight:
                raise Exception('Tatami fight not found')

            taken_tatami_fight.fight_id = None
            taken_tatami_fight.status = TatamiStatus.FREE

            fight_duration = end_time - start_time
            athlete_id = int(data.get('winner_athlete_id'))
            new_result = ResultNew(
                fight_id = fight_id,
                winner_id = athlete_id,
                victory_type = data.get('victory_type'),
                fight_duration = int(fight_duration.total_seconds()),
                count_of_fights_win = 1
            )

            self.move_athlete_next_fight(fight_id,athlete_id)

            self.session.add(new_result)
            self.session.commit()
        except Exception as e:
            print('Error: ', e)
            self.session.rollback()

    def move_athlete_next_fight(self, fight_id, athlete_id):
        try:
            fight = self.get_fight_by_id(fight_id)

            if not fight.next_fight_id:
                return

            next_fight = self.get_fight_by_id(fight.next_fight_id)

            if not fight or not next_fight:
                raise Exception('Error: Fight or next fight not found')

            if fight.blue_athlete_id == athlete_id and not next_fight.white_athlete_id:
                next_fight.white_athlete_id = athlete_id
            elif fight.white_athlete_id == athlete_id and not next_fight.blue_athlete_id:
                next_fight.blue_athlete_id = athlete_id
            elif not next_fight.white_athlete_id:
                next_fight.white_athlete_id = athlete_id
            elif not next_fight.blue_athlete_id:
                next_fight.blue_athlete_id = athlete_id
            else:
                print('Error: Athlete not found in the fight')
                return

            self.session.commit()
        except Exception as e:
            print('Error: ', e)
            self.session.rollback()

    def get_semi_final_fights(self, tournament_category_id, semi_final_round_number):
        semi_final_fights = (
            self.session.query(FightNew)
            .filter(
                FightNew.tournament_category_id == tournament_category_id,
                FightNew.round_number <=  semi_final_round_number
            )
            .all()
        )
        return semi_final_fights

    def get_final_fights(self, tournament_category_id, final_round_number):
        semi_final_fights = (
            self.session.query(FightNew)
            .filter(
                FightNew.tournament_category_id == tournament_category_id,
                FightNew.round_number ==  final_round_number
            )
            .all()
        )
        return semi_final_fights

    def _text_to_time(self,text):
        try:
            m, s = map(int, text.split(":"))
            return timedelta(minutes=m, seconds=s)
        except Exception as e:
            print('Error: ', e)
            return None

    def create_result(self,  result):
        try:
            self.session.add(result)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print('Error: ', e)

    def update_end_time(self, fight_id, end_time:timedelta):
        try:
            fight = self.get_fight_by_id(fight_id)
            if fight:
                fight.end_time = end_time
                self.session.commit()
        except Exception as e:
            print('Error: ', e)
            self.session.rollback()