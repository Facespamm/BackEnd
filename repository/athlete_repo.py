from datetime import datetime

from sqlalchemy import or_

from database.db import create_session
from new_model.head_model.new_athlete import AthleteNew
from new_model.head_model.new_user import UserNew


class AthleteRepository:
    def __init__(self):
        self.session = create_session()

    def get_athletes(self, club_id:int, search_name: str):
        query = self.session.query(AthleteNew).join(AthleteNew.user).filter_by(is_active = True)

        if club_id:
            query = query.filter(AthleteNew.club_id == club_id)

        if search_name:
            query = query.filter(
                or_(
                    UserNew.last_name.ilike(f'%{search_name}%'),
                    UserNew.first_name.ilike(f'%{search_name}%')
                )
            )

        athletes = query.order_by(UserNew.last_name, UserNew.first_name).all()
        return athletes

    def get_athletes_by_tournament(self, tournament_id:int):
        query = self.session.query(AthleteNew).join(AthleteNew.tournaments).filter(
            AthleteNew.is_active == True,
            AthleteNew.tournaments.any(id=tournament_id)
        )

        athletes = query.order_by(AthleteNew.user.has().last_name, AthleteNew.user.has().first_name).all()
        return athletes

    def get_victory_count(self,  athlete_id:int, tournament_id = None):
        from new_model.result_new import ResultNew
        from new_model.head_model.fight_new import FightNew

        count_query = self.session.query(ResultNew).join(FightNew, ResultNew.fight_id == FightNew.id).filter(
            ResultNew.winner_id == athlete_id,
        )

        if tournament_id is not None:
            count_query = count_query.filter(FightNew.tournament_id == tournament_id)

        count = count_query.count()
        return count


    def create_athlete(self, athlete:AthleteNew):
        try:
            self.session.add(athlete)
            self.session.commit()
            return True
        except Exception as e:
            print(f'Error create athlete: {e}')
            self.session.rollback()
            return False

    def get_athlete_by_id(self, athlete_id:int):
        return self.session.query(AthleteNew).join(AthleteNew.user).filter_by(id = athlete_id).first()

    def update_athlete(self, athlete:AthleteNew, athlete_fields:list,user_fields:list, data: dict):
        try:
            user = athlete.user

            for field in user_fields:
                if field in data:
                    value = data[field]
                    if isinstance(value, str):
                        value = value.strip() if value else None
                    setattr(user, field, value)

            for field in athlete_fields:
                if field in data:
                    value = data[field]
                    if field == 'birth_date' and isinstance(value, str):
                        value = datetime.fromisoformat(value).date()
                    setattr(athlete, field, value)

            self.session.commit()
            return True
        except Exception as e:
            print(f'Error update athlete: {e}')
            self.session.rollback()
            return False

    def delete_athlete_by_id(self, athlete:AthleteNew):
        try:
            athlete.is_active = False
            athlete.user.is_active = False

            self.session.commit()
            return True
        except Exception as e:
            print(f'Error delete athlete: {e}')
            self.session.rollback()
            return False