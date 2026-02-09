from datetime import datetime

from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload

from database.db import create_session
from new_model.Enums import RoleName
from new_model.handbook.new_dan import DanNew
from new_model.handbook.role_new import RoleNew
from new_model.head_model.fight_new import FightNew
from new_model.head_model.new_athlete import AthleteNew
from new_model.head_model.new_user import UserNew
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

    def get_basic_info(self,club_id:int, search_name: str):
        query = (
            self.session.query(AthleteNew.id,UserNew.first_name, UserNew.last_name,UserNew.middle_name, DanNew.level)
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

    def search_athletes_by_name(self, name_query: dict, club_id=None):
        """
        Поиск активных спортсменов по ФИО (частичное совпадение).
        Поддерживает фильтр по клубу (club_id=None — поиск по всем клубам).
        """
        # Базовый запрос с обязательным JOIN к UserNew для фильтрации и сортировки
        query = (
            self.session.query(AthleteNew.id,UserNew.id,UserNew.first_name,UserNew.last_name,UserNew.middle_name,DanNew.level)
            .join(AthleteNew.user)
            .join(AthleteNew.rank)
            .filter(AthleteNew.is_active == True)
        )

        # Фильтр по клубу
        if club_id is not None and club_id != '':
            query = query.filter(AthleteNew.club_id == club_id)

        # Фильтрация по ФИО
        if name_query:
            first_name = name_query.get('first_name')
            middle_name = name_query.get('middle_name')
            last_name = name_query.get('last_name')

            if first_name:
                query = query.filter(UserNew.first_name.ilike(f'%{first_name}%'))
            if middle_name:
                query = query.filter(UserNew.middle_name.ilike(f'%{middle_name}%'))
            if last_name:
                query = query.filter(UserNew.last_name.ilike(f'%{last_name}%'))

        # Сортировка по фамилии и имени
        query = query.order_by(UserNew.last_name, UserNew.first_name)

        athletes = query.all()
        return athletes

    def get_athletes_by_club_id(self, club_id: int, tournament_id=None, include_tournament_info=False):
        # Базовый запрос с обязательным join(user) для сортировки и joinedload для подгрузки
        athletes_query = (
            self.session.query(AthleteNew)
            .join(AthleteNew.user)  # ← Обязательно добавляем join для order_by по полям user
            .options(
                joinedload(AthleteNew.rank),
                joinedload(AthleteNew.club),
                joinedload(AthleteNew.user)
            )
            .filter(
                AthleteNew.is_active == True,
                AthleteNew.club_id == club_id,
            )
        )

        # Фильтр по tournament_id (если передан) — только зарегистрированные в турнире
        if tournament_id is not None:
            athletes_query = athletes_query \
                .join(AthleteRegistration, AthleteNew.id == AthleteRegistration.athlete_id) \
                .join(TournamentCategory,
                      AthleteRegistration.tournament_category_id == TournamentCategory.tournament_category_id) \
                .filter(TournamentCategory.tournament_id == tournament_id)

        # Подгрузка информации о турнирах (независимо от tournament_id)
        if include_tournament_info:
            athletes_query = athletes_query.options(
                joinedload(AthleteNew.registrations)  # ← ИСПРАВЛЕНО: plural "registrations"
                .joinedload(AthleteRegistration.tournament_categories)
                .joinedload(TournamentCategory.tournament)
            )

        # Сортировка (теперь работает благодаря join(user))
        athletes = athletes_query.order_by(
            UserNew.last_name, UserNew.first_name
        ).all()

        return athletes

    def set_category(self, athlete:AthleteNew,weigth):
        category_repo = CategoryRepository()
        category_id = category_repo.get_id_by_athlete_feature(weigth, athlete.birth_date.year, athlete.gender)

        if not category_id:
            raise Exception('Не найдина категория')

        athlete.category_id = category_id

    def get_athlete_by_fight(self,  athlete_id:int ,fight_id:int):
        athlete = (
            self.session.query(AthleteNew.id,UserNew.first_name, UserNew.last_name, UserNew.middle_name, AthleteNew.gender)
            .join(AthleteNew, AthleteNew.user_id == UserNew.id)
            .join(FightNew, or_(
            FightNew.white_athlete_id == AthleteNew.id,
            FightNew.blue_athlete_id == AthleteNew.id
            ))
            .filter(
                FightNew.id == fight_id,
                AthleteNew.id == athlete_id
            ).first()
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

    def get_winer_data(self, athlete_id):
        result = (
            self.session.query(UserNew.last_name, UserNew.first_name, UserNew.middle_name)
            .join(AthleteNew, AthleteNew.user_id == UserNew.id)
            .filter(AthleteNew.id == athlete_id)
            .first()
        )

        if result:
            return {
                'last_name': result[0],
                'first_name': result[1],
                'middle_name': result[2]
            }
        return None

    def update_category(self, athlete_id:int, weight):
        try:
            athlete = self.get_athlete_by_id(athlete_id)

            if not athlete:
                return False

            self.set_category(athlete, weight)
            self.session.commit()
            return True
        except Exception as e:
            print('Error ',e)
            self.session.rollback()
            return False