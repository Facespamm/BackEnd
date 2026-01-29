from datetime import datetime

from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload

from database.db import create_session
from new_model.Enums import RoleName
from new_model.handbook.role_new import RoleNew
from new_model.head_model.new_athlete import AthleteNew
from new_model.head_model.new_user import UserNew
from new_model.head_model.tournament_new import TournamentNew
from new_model.new_associations import AthleteRegistration, TournamentCategory, new_user_roles
from repository.category_repo import CategoryRepository


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

    def get_athletes_by_tournament(self, tournament_id:int, category_id: int):
        query = (
            self.session.query(AthleteNew)
            .join(AthleteRegistration, AthleteNew.id == AthleteRegistration.athlete_id)
            .join(TournamentCategory, AthleteRegistration.tournament_category_id == TournamentCategory.tournament_category_id)
            .filter(
                AthleteNew.is_active == True,
                TournamentCategory.tournament_id == tournament_id,
                TournamentCategory.category_id == category_id,
            )
        )

        athletes = query.order_by(AthleteNew.id).all()
        return athletes

    def count_athletes_in_club(self, club_id: int) -> int:
        """
        Возвращает количество активных спортсменов в указанном клубе.

        :param club_id: Идентификатор клуба
        :return: Количество активных спортсменов
        """
        count = (
            self.session.query(AthleteNew)
            .filter(
                AthleteNew.club_id == club_id,
                AthleteNew.is_active == True
            )
            .count()
        )
        return count

    def get_victory_count(self,  athlete_id:int, tournament_id = None):
        from new_model.result_new import ResultNew
        from new_model.head_model.fight_new import FightNew

        if hasattr(athlete_id, 'id'):
            athlete_id = athlete_id.id

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
        return self.session.query(AthleteNew).join(AthleteNew.user).filter(AthleteNew.id == athlete_id).first()

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

    def delete_athlete(self, athlete:AthleteNew):
        try:
            athlete.is_active = False
            athlete.user.is_active = False

            self.session.commit()
            return True
        except Exception as e:
            print(f'Error delete athlete: {e}')
            self.session.rollback()
            return False

    def has_athlete(self, user_id:int):
        athlete = (
            self.session.query(AthleteNew)
            .join(new_user_roles, AthleteNew.user_id == new_user_roles.c.user_id)
            .join(RoleNew, new_user_roles.c.role_id == RoleNew.id)
            .filter(
                and_(
                    AthleteNew.user_id == user_id,
                    AthleteNew.is_active == True,
                    RoleNew.name == RoleName.ATHLETE.value
                )
            ).first()
        )

        return athlete is not None

    def search_athletes_by_name(self, name_query:dict, club_id = None):
        query = (
            self.session.query(AthleteNew)
            .options(joinedload(AthleteNew.rank), joinedload(AthleteNew.user),joinedload(AthleteNew.club))
            .filter(
                AthleteNew.is_active == True,
            )
        )

        if club_id:
            query = query.filter(AthleteNew.club_id == club_id)

        if name_query:
            first_name = name_query.get('first_name', None).strip()
            middle_name = name_query.get('middle_name', None).strip()
            last_name = name_query.get('last_name', None).strip()

            if first_name:
                query = query.filter(UserNew.first_name.ilike(f'%{first_name}%'))
            if middle_name:
                query = query.filter(UserNew.middle_name.ilike(f'%{middle_name}%'))
            if last_name:
                query = query.filter(UserNew.last_name.ilike(f'%{last_name}%'))

        athletes = query.order_by(AthleteNew.user.last_name, AthleteNew.user.first_name).all()
        return athletes

    def get_athletes_by_club_id(self, club_id:int, tournament_id = None, include_tournament_info = False):
        athletes_query = (
            self.session.query(AthleteNew)
            .options(joinedload(AthleteNew.rank), joinedload(AthleteNew.club), joinedload(AthleteNew.user))
            .filter(
                AthleteNew.is_active == True,
                AthleteNew.club_id == club_id,
            )
        )

        if not tournament_id and not include_tournament_info:
            athletes_query = (
                athletes_query
                .join(AthleteRegistration)
                .join(TournamentCategory, AthleteRegistration.tournament_category_id == TournamentCategory.tournament_category_id)
                .join(TournamentNew, TournamentCategory.tournament_id == TournamentNew.id)
                # .filter(TournamentNew.id == tournament_id)
            )
        elif tournament_id and include_tournament_info:
            athletes_query = (
                athletes_query
                .join(AthleteRegistration)
                .join(TournamentCategory, AthleteRegistration.tournament_category_id == TournamentCategory.tournament_category_id)
                .join(TournamentNew, TournamentCategory.tournament_id == TournamentNew.id)
                .filter(TournamentNew.id == tournament_id)
                .options(
                    joinedload(AthleteNew.registration)
                    .joinedload(AthleteRegistration.tournament_categories)
                    .joinedload(TournamentCategory.tournament)
                         )
            )
        elif tournament_id and not include_tournament_info:
            athletes_query = (
                athletes_query
                .join(AthleteRegistration)
                .join(TournamentCategory, AthleteRegistration.tournament_category_id == TournamentCategory.tournament_category_id)
                .join(TournamentNew, TournamentCategory.tournament_id == TournamentNew.id)
                .filter(TournamentNew.id == tournament_id)
            )

        athletes = athletes_query.order_by(AthleteNew.user.last_name, AthleteNew.user.first_name).all()
        return athletes

    def set_category(self, athlete:AthleteNew,weigth):
        category_repo = CategoryRepository()
        category_id = category_repo.get_id_by_athlete_feature(weigth, athlete.age, athlete.gender)

        if not category_id:
            raise Exception('Не найдина категория')

        athlete.category_id = category_id