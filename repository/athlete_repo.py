from datetime import datetime

from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload

from database.db import get_session
from new_model.Enums import RoleName
from new_model.handbook.new_dan import DanNew
from new_model.handbook.role_new import RoleNew
from new_model.head_model.fight_new import FightNew
from new_model.head_model.new_athlete import AthleteNew
from new_model.head_model.new_user import UserNew
from new_model.new_associations import AthleteRegistration, TournamentCategory, new_user_roles
from repository.category_repo import CategoryRepository


class AthleteRepository:
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

    def get_athletes(self, club_id: int, search_name: str):
        query = self.session.query(AthleteNew).join(AthleteNew.user).filter_by(is_active=True)
        if club_id:
            query = query.filter(AthleteNew.club_id == club_id)
        if search_name:
            query = query.filter(
                or_(
                    UserNew.last_name.ilike(f'%{search_name}%'),
                    UserNew.first_name.ilike(f'%{search_name}%')
                )
            )
        return query.order_by(UserNew.last_name, UserNew.first_name).all()

    def get_basic_info(self, club_id: int, search_name: str):
        query = (
            self.session.query(AthleteNew.id, UserNew.first_name, UserNew.last_name, UserNew.middle_name, DanNew.level)
            .join(AthleteNew.user)
            .join(AthleteNew.rank)
            .filter(AthleteNew.is_active == True)
        )
        if club_id:
            query = query.filter(AthleteNew.club_id == club_id)
        if search_name:
            query = query.filter(
                or_(
                    UserNew.last_name.ilike(f'%{search_name}%'),
                    UserNew.first_name.ilike(f'%{search_name}%')
                )
            )
        return query.order_by(UserNew.last_name, UserNew.first_name).all()

    def get_athletes_by_tournament(self, tournament_id: int, category_id: int):
        return (
            self.session.query(AthleteNew)
            .join(AthleteRegistration, AthleteNew.id == AthleteRegistration.athlete_id)
            .join(TournamentCategory, AthleteRegistration.tournament_category_id == TournamentCategory.tournament_category_id)
            .filter(
                AthleteNew.is_active == True,
                TournamentCategory.tournament_id == tournament_id,
                TournamentCategory.category_id == category_id,
            )
            .order_by(AthleteNew.id)
            .all()
        )

    def count_athletes_in_club(self, club_id: int) -> int:
        return (
            self.session.query(AthleteNew)
            .filter(AthleteNew.club_id == club_id, AthleteNew.is_active == True)
            .count()
        )

    def get_victory_count(self, athlete_id: int, tournament_id=None):
        from new_model.result_new import ResultNew
        if hasattr(athlete_id, 'id'):
            athlete_id = athlete_id.id
        query = (
            self.session.query(ResultNew)
            .join(FightNew, ResultNew.fight_id == FightNew.id)
            .filter(ResultNew.winner_id == athlete_id)
        )
        if tournament_id is not None:
            query = query.filter(FightNew.tournament_id == tournament_id)
        return query.count()

    def create_athlete(self, athlete: AthleteNew):
        try:
            self.session.add(athlete)
            self.session.commit()
            return True
        except Exception as e:
            print(f'Error create athlete: {e}')
            self.session.rollback()
            return False

    def get_athlete_by_id(self, athlete_id: int):
        return self.session.query(AthleteNew).join(AthleteNew.user).filter(AthleteNew.id == athlete_id).first()

    def update_athlete(self, athlete: AthleteNew, athlete_fields: list, user_fields: list, data: dict):
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

    def delete_athlete(self, athlete: AthleteNew):
        try:
            athlete.is_active = False
            athlete.user.is_active = False
            self.session.commit()
            return True
        except Exception as e:
            print(f'Error delete athlete: {e}')
            self.session.rollback()
            return False

    def has_athlete(self, user_id: int):
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

    def search_athletes_by_name(self, name_query: dict, club_id=None):
        query = (
            self.session.query(AthleteNew.id, UserNew.id, UserNew.first_name, UserNew.last_name, UserNew.middle_name, DanNew.level)
            .join(AthleteNew.user)
            .join(AthleteNew.rank)
            .filter(AthleteNew.is_active == True)
        )
        if club_id is not None and club_id != '':
            query = query.filter(AthleteNew.club_id == club_id)
        if name_query:
            if name_query.get('first_name'):
                query = query.filter(UserNew.first_name.ilike(f'%{name_query["first_name"]}%'))
            if name_query.get('middle_name'):
                query = query.filter(UserNew.middle_name.ilike(f'%{name_query["middle_name"]}%'))
            if name_query.get('last_name'):
                query = query.filter(UserNew.last_name.ilike(f'%{name_query["last_name"]}%'))
        return query.order_by(UserNew.last_name, UserNew.first_name).all()

    def get_athletes_by_club_id(self, club_id: int, tournament_id=None, include_tournament_info=False):
        athletes_query = (
            self.session.query(AthleteNew)
            .join(AthleteNew.user)
            .options(
                joinedload(AthleteNew.rank),
                joinedload(AthleteNew.club),
                joinedload(AthleteNew.user)
            )
            .filter(AthleteNew.is_active == True, AthleteNew.club_id == club_id)
        )
        if tournament_id is not None:
            athletes_query = (
                athletes_query
                .join(AthleteRegistration, AthleteNew.id == AthleteRegistration.athlete_id)
                .join(TournamentCategory, AthleteRegistration.tournament_category_id == TournamentCategory.tournament_category_id)
                .filter(TournamentCategory.tournament_id == tournament_id)
            )
        if include_tournament_info:
            athletes_query = athletes_query.options(
                joinedload(AthleteNew.registrations)
                .joinedload(AthleteRegistration.tournament_categories)
                .joinedload(TournamentCategory.tournament)
            )
        return athletes_query.order_by(UserNew.last_name, UserNew.first_name).all()

    def set_category(self, athlete: AthleteNew, weigth):
        category_repo = CategoryRepository(self.session)
        category_id = category_repo.get_id_by_athlete_feature(weigth, athlete.birth_date.year, athlete.gender)
        if not category_id:
            raise Exception('Не найдена категория')
        athlete.category_id = category_id

    def get_athlete_by_fight(self, athlete_id: int, fight_id: int):
        athlete = (
            self.session.query(AthleteNew.id, UserNew.first_name, UserNew.last_name, UserNew.middle_name, AthleteNew.gender)
            .join(AthleteNew, AthleteNew.user_id == UserNew.id)
            .join(FightNew, or_(
                FightNew.white_athlete_id == AthleteNew.id,
                FightNew.blue_athlete_id == AthleteNew.id
            ))
            .filter(FightNew.id == fight_id, AthleteNew.id == athlete_id)
            .first()
        )
        if not athlete:
            return None
        return {
            'id': athlete[0],
            'first_name': athlete[1],
            'last_name': athlete[2],
            'middle_name': athlete[3],
            'gender': athlete[4]
        }

    def get_athlete_name_data(self, athlete_id):
        result = (
            self.session.query(UserNew.last_name, UserNew.first_name, UserNew.middle_name)
            .join(AthleteNew, AthleteNew.user_id == UserNew.id)
            .filter(AthleteNew.id == athlete_id)
            .first()
        )
        if result:
            return {'last_name': result[0], 'first_name': result[1], 'middle_name': result[2]}
        return None

    def update_category(self, athlete_id: int, weight):
        try:
            athlete = self.get_athlete_by_id(athlete_id)
            if not athlete:
                return False
            self.set_category(athlete, weight)
            self.session.commit()
            return True
        except Exception as e:
            print('Error ', e)
            self.session.rollback()
            return False

    def get_athlete_id_by_user(self, user_id):
        try:
            athlete_id = self.session.query(AthleteNew.id).filter(AthleteNew.user_id == user_id).scalar()
            return athlete_id
        except Exception as e:
            print('Error ', e)
            return None