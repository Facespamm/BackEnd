from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload

from database.db import get_session
from models.AthleteTournamentRegistration import AthleteTournamentRegistration
from models.Enums import RoleName
from models.fight_new import FightNew
from models.new_associations import (
    AthleteRegistration,
    TournamentCategory,
    new_user_roles,
)
from models.new_athlete import AthleteNew
from models.new_dan import DanNew
from models.new_user import UserNew
from models.role_new import RoleNew
from repository.category_repo import CategoryRepository
from routers.athletes.schemas import UpdateAthleteRequest


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
        query = (
            self.session.query(AthleteNew)
            .join(AthleteNew.user)
            .filter_by(is_active=True)
        )

        if club_id:
            query = query.filter(AthleteNew.club_id == club_id)
        if search_name:
            query = query.filter(
                or_(
                    UserNew.last_name.ilike(f"%{search_name}%"),
                    UserNew.first_name.ilike(f"%{search_name}%"),
                )
            )
        return query.order_by(UserNew.last_name, UserNew.first_name).all()

    def get_athlete_for_registrations_on_club(self):
        return (
            self.session.query(AthleteNew)
            .options(joinedload(AthleteNew.user), joinedload(AthleteNew.club))
            .filter(AthleteNew.is_active == True)
            .all()
        )

    def get_basic_info(
        self, club_id: int, search_name: str, tournament_id: int | None = None
    ):
        query = (
            self.session.query(
                AthleteNew.id,
                UserNew.first_name,
                UserNew.last_name,
                UserNew.middle_name,
                DanNew.level,
                AthleteNew.gender,
                AthleteNew.age,
            )
            .join(AthleteNew.user)
            .outerjoin(AthleteNew.rank)
            .filter(AthleteNew.is_active == True)
        )

        if tournament_id is not None:
            registered_ids = (
                self.session.query(AthleteTournamentRegistration.athlete_id)
                .filter_by(tournament_id=tournament_id)
                .scalar_subquery()
            )

            query = query.filter(AthleteNew.id.not_in(registered_ids))

        if club_id:
            query = query.filter(AthleteNew.club_id == club_id)
        if search_name:
            query = query.filter(
                or_(
                    UserNew.last_name.ilike(f"%{search_name}%"),
                    UserNew.first_name.ilike(f"%{search_name}%"),
                )
            )
        return query.order_by(UserNew.last_name, UserNew.first_name).all()

    def get_athletes_by_tournament(self, tournament_id: int, category_id: int):
        return (
            self.session.query(AthleteNew)
            .join(AthleteRegistration, AthleteNew.id == AthleteRegistration.athlete_id)
            .join(
                TournamentCategory,
                AthleteRegistration.tournament_category_id
                == TournamentCategory.tournament_category_id,
            )
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
        from models.result_new import ResultNew

        if hasattr(athlete_id, "id"):
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
            print(f"Error create athlete: {e}")
            self.session.rollback()
            return False

    def get_athlete_by_id(self, athlete_id: int):
        return (
            self.session.query(AthleteNew)
            .join(AthleteNew.user)
            .filter(AthleteNew.id == athlete_id)
            .first()
        )

    def update_athlete(self, athlete: AthleteNew, update_athlete: UpdateAthleteRequest):
        try:
            user = athlete.user

            user.first_name = (
                update_athlete.first_name.strip() if update_athlete.first_name else None
            )
            user.last_name = (
                update_athlete.last_name.strip() if update_athlete.last_name else None
            )
            user.middle_name = (
                update_athlete.middle_name.strip()
                if update_athlete.middle_name
                else None
            )
            user.phone = update_athlete.phone.strip() if update_athlete.phone else None
            user.email = update_athlete.email

            for field, value in update_athlete.model_dump(
                exclude={"first_name", "last_name", "middle_name", "phone", "email"}
            ).items():
                setattr(athlete, field, value)

            self.session.commit()
            return True
        except Exception as e:
            print(f"Error update athlete: {e}")
            self.session.rollback()
            return False

    def delete_athlete(self, athlete: AthleteNew):
        try:
            athlete.is_active = False
            athlete.user.is_active = False
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error delete athlete: {e}")
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
                    RoleNew.name == RoleName.ATHLETE.value,
                )
            )
            .first()
        )
        return athlete is not None

    def search_athletes_by_name(self, name_query: dict, club_id=None):
        query = (
            self.session.query(AthleteNew)
            .join(AthleteNew.user)
            .options(joinedload(AthleteNew.user))
            .filter(AthleteNew.is_active == True)
        )
        if club_id is not None and club_id != "":
            query = query.filter(AthleteNew.club_id == club_id)
        if name_query:
            if name_query.get("first_name"):
                query = query.filter(
                    UserNew.first_name.ilike(f"%{name_query['first_name']}%")
                )
            if name_query.get("middle_name"):
                query = query.filter(
                    UserNew.middle_name.ilike(f"%{name_query['middle_name']}%")
                )
            if name_query.get("last_name"):
                query = query.filter(
                    UserNew.last_name.ilike(f"%{name_query['last_name']}%")
                )
        return query.order_by(UserNew.last_name, UserNew.first_name).all()

    def get_athletes_by_club_id(
        self, club_id: int, tournament_id=None, include_tournament_info=False
    ):
        athletes_query = (
            self.session.query(AthleteNew)
            .join(AthleteNew.user)
            .options(
                joinedload(AthleteNew.rank),
                joinedload(AthleteNew.club),
                joinedload(AthleteNew.user),
            )
            .filter(AthleteNew.is_active == True, AthleteNew.club_id == club_id)
        )
        if tournament_id is not None:
            athletes_query = (
                athletes_query.join(
                    AthleteRegistration, AthleteNew.id == AthleteRegistration.athlete_id
                )
                .join(
                    TournamentCategory,
                    AthleteRegistration.tournament_category_id
                    == TournamentCategory.tournament_category_id,
                )
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
        category_id = category_repo.get_id_by_athlete_feature(
            weigth, athlete.birth_date.year, athlete.gender
        )
        if not category_id:
            raise Exception("Не найдена категория")
        athlete.category_id = category_id

    def get_athlete_by_fight(self, athlete_id: int, fight_id: int):
        athlete = (
            self.session.query(
                AthleteNew.id.label("id"),
                UserNew.first_name.label("first_name"),
                UserNew.last_name.label("last_name"),
                UserNew.middle_name.label("middle_name"),
                AthleteNew.gender.label("gender"),
            )
            .join(UserNew, AthleteNew.user_id == UserNew.id)
            .join(
                FightNew,
                or_(
                    FightNew.white_athlete_id == AthleteNew.id,
                    FightNew.blue_athlete_id == AthleteNew.id,
                ),
            )
            .filter(FightNew.id == fight_id, AthleteNew.id == athlete_id)
            .first()
        )

        if not athlete:
            return None

        return {
            "id": athlete.id,
            "first_name": athlete.first_name,
            "last_name": athlete.last_name,
            "middle_name": athlete.middle_name,
            "gender": athlete.gender.value
            if hasattr(athlete.gender, "value")
            else athlete.gender,
        }

    def get_athlete_name_data(self, athlete_id):
        result = (
            self.session.query(
                UserNew.last_name.label("last_name"),
                UserNew.first_name.label("first_name"),
                UserNew.middle_name.label("middle_name"),
            )
            .join(AthleteNew, AthleteNew.user_id == UserNew.id)
            .filter(AthleteNew.id == athlete_id)
            .first()
        )
        if result:
            return {
                "last_name": result.last_name,
                "first_name": result.first_name,
                "middle_name": result.middle_name,
            }
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
            print("Error ", e)
            self.session.rollback()
            return False

    def get_athlete_id_by_user(self, user_id):
        try:
            athlete_id = (
                self.session.query(AthleteNew.id)
                .filter(AthleteNew.user_id == user_id)
                .scalar()
            )
            return athlete_id
        except Exception as e:
            print("Error ", e)
            return None
