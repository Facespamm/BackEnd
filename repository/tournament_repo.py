from sqlalchemy import and_, extract, delete
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.functions import count

from database.db import get_session
from new_model.AthleteTournamentRegistration import AthleteTournamentRegistration
from new_model.Enums import StatusTournamentRegistration
from new_model.handbook.category_new import CategoryNew
from new_model.head_model.new_athlete import AthleteNew
from new_model.head_model.tournament_new import TournamentNew
from new_model.new_associations import TournamentCategory, AthleteRegistration
from new_model.tatami_fight import TatamiFight
from repository.category_repo import CategoryRepository


class TournamentRepository:
    def __init__(self, session = None):
        self.session = session if session else get_session()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        self.session.close()

    def add_club_to_tournament(self, tournament_id, club_id):
        """Добавить всех подходящих атлетов клуба на турнир (предварительная регистрация)"""
        try:
            tournament = self.get_tournament_by_id(tournament_id)
            if not tournament:
                raise ValueError(f"Tournament with id {tournament_id} not found")

            categories = self.get_categories(tournament.id)
            if not categories:
                raise ValueError(f"No categories found for tournament {tournament_id}")

            category_ids = [cat.id for cat in categories]

            # Получаем атлетов клуба, которые подходят по возрасту/полу хотя бы к одной категории
            athletes_query = (
                self.session.query(AthleteNew)
                .filter(AthleteNew.club_id == club_id)
                .join(CategoryNew, and_(
                    extract('year', AthleteNew.birth_date) >= CategoryNew.min_year,
                    extract('year', AthleteNew.birth_date) <= CategoryNew.max_year,
                    CategoryNew.gender == AthleteNew.gender,
                    CategoryNew.id.in_(category_ids)
                ))
                .distinct(AthleteNew.id)   # убираем дубликаты
            )

            athletes = athletes_query.all()

            if not athletes:
                raise ValueError(f"No suitable athletes found from club {club_id} for tournament {tournament_id}")

            # Получаем уже зарегистрированных на турнир
            existing_reg_ids = {
                row[0] for row in
                self.session.query(AthleteTournamentRegistration.athlete_id)
                .filter_by(tournament_id=tournament_id)
                .all()
            }

            added_count = 0
            for athlete in athletes:
                if athlete.id in existing_reg_ids:
                    continue

                reg = AthleteTournamentRegistration(
                    athlete_id=athlete.id,
                    tournament_id=tournament_id
                )
                self.session.add(reg)
                added_count += 1

            self.session.commit()

            print(f"Added {added_count} athletes from club {club_id} to tournament {tournament_id}")
            return added_count

        except Exception as e:
            self.session.rollback()
            print(f"Error adding club {club_id} to tournament {tournament_id}: {e}")
            raise

    def get_preliminary_registrations(self, tournament_id: int, status: StatusTournamentRegistration | None = None):
        """Получить предварительно зарегистрированных атлетов на турнир"""
        query = (
            self.session.query(AthleteTournamentRegistration, AthleteNew)
            .join(AthleteNew, AthleteNew.id == AthleteTournamentRegistration.athlete_id)
            .options(joinedload(AthleteNew.user), joinedload(AthleteNew.club), joinedload(AthleteNew.rank))
            .filter(AthleteTournamentRegistration.tournament_id == tournament_id)
        )

        if status:
            query = query.filter(AthleteTournamentRegistration.status == status)

        results = query.all()

        athletes_data = []
        for athlete_tournament_registration, athlete in results:
            athletes_data.append({
                'athlete': athlete
            })

        return athletes_data

    def get_weighed_athletes(self, tournament_id, category_id=None):
        """Получить зарегистрированных атлетов на турнир"""
        try:
            query = (
                self.session.query(AthleteNew, CategoryNew, TournamentCategory)
                .join(AthleteRegistration, AthleteRegistration.athlete_id == AthleteNew.id)
                .join(TournamentCategory,
                      TournamentCategory.tournament_category_id == AthleteRegistration.tournament_category_id)
                .join(CategoryNew, CategoryNew.id == TournamentCategory.category_id)
                .options(
                    joinedload(AthleteNew.user),
                    joinedload(AthleteNew.club),
                    joinedload(AthleteNew.rank)
                )
                .filter(TournamentCategory.tournament_id == tournament_id)
            )

            # Фильтрация по категории, если передана
            if category_id:
                query = query.filter(TournamentCategory.category_id == category_id)

            results = query.all()

            athletes_data = []
            for athlete, category, tournament_category in results:
                athletes_data.append({
                    'athlete': athlete,
                    'category': category,
                    'tournament_category': tournament_category
                })

            return athletes_data

        except Exception as e:
            print(f"Error getting tournament athletes: {e}")
            return []

    def add_athlete_to_tournament(self, tournament_id, athlete_id):
        """Добавить атлета на турнир (предварительная регистрация)"""
        try:
            tournament = self.get_tournament_by_id(tournament_id)
            if not tournament:
                raise ValueError(f"Tournament with id {tournament_id} not found")

            athlete = self.session.query(AthleteNew).filter_by(id=athlete_id).first()
            if not athlete:
                raise ValueError(f"Athlete with id {athlete_id} not found")

            # Проверяем, что атлет ещё не зарегистрирован на этот турнир
            existing = self.session.query(AthleteTournamentRegistration).filter_by(
                tournament_id=tournament_id,
                athlete_id=athlete_id
            ).first()

            if existing:
                if existing.status == StatusTournamentRegistration.REGISTERED:
                    print(f"Athlete {athlete_id} already registered for tournament {tournament_id}")
                    return False

            # Создаём предварительную регистрацию
            reg = AthleteTournamentRegistration(
                athlete_id=athlete_id,
                tournament_id=tournament_id,
            )
            self.session.add(reg)
            self.session.commit()

            print(f"Athlete {athlete_id} successfully registered to tournament {tournament_id}")
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error adding athlete {athlete_id} to tournament {tournament_id}: {e}")
            raise

    def get_tournament_by_id(self, tournament_id):
        """Получить турнир по ID"""
        try:
            tournament = (
                self.session.query(TournamentNew)
                .options(joinedload(TournamentNew.tournament_categories).joinedload(TournamentCategory.category))
                .filter_by(id=tournament_id).one_or_none()
            )

            if not tournament:
                print(f"Tournament with id {tournament_id} not found")
                return None

            return tournament
        except Exception as e:
            print(f"Error getting tournament by id {tournament_id}: {e}")
            return None

    def get_athletes_by_tournament(self, tournament_id):
        tournament = self.get_tournament_by_id(tournament_id)

        if not tournament:
            return None

        athletes = tournament.athletes
        return athletes

    def get_all_tournaments(self, status=None):
        """Получить все турниры"""
        try:
            tournaments_query = self.session.query(TournamentNew).filter_by(is_active = True).order_by(TournamentNew.start_date.desc())

            if status:
                tournaments_query = tournaments_query.filter_by(status=status)

            tournaments = tournaments_query.all()
            return tournaments
        except Exception as e:
            print(f"Error getting all tournaments: {e}")
            return []

    def get_athlete_count(self, tournament_id):
        """Количество участников на турнир"""
        try:
            count_athlete = (
                self.session.query(count(AthleteRegistration.athlete_id))
                .join(TournamentCategory)
                .filter(
                    TournamentCategory.tournament_id == tournament_id
                ).scalar()
            )

            return count_athlete if count_athlete else 0
        except Exception as e:
            print(f"Error getting athlete count: {e}")
            return None

    def get_register_athlete_count(self, tournament_id):
        """Количество участников на турнир"""
        try:
            count_athlete = (
                self.session.query(count(AthleteTournamentRegistration.athlete_id))
                .filter(
                    AthleteTournamentRegistration.tournament_id == tournament_id
                ).scalar()
            )

            return count_athlete if count_athlete else 0
        except Exception as e:
            print(f"Error getting athlete count: {e}")
            return None

    def get_categories(self, tournament_id) -> list[CategoryNew] | None:
        """Категории по турниру"""
        try:
            categories = (
                self.session.query(CategoryNew)
                .join(TournamentCategory)
                .filter(TournamentCategory.tournament_id == tournament_id)
                .all()
            )

            return categories
        except Exception as e:
            print(f"Error getting category: {e}")
            return None

    def get_tournament_categories(self, tournament_id: int):
        return (
            self.session.query(TournamentCategory)
            .filter(TournamentCategory.tournament_id == tournament_id)
            .all()
        )

    def get_category(self, tournament_id, category_id) -> CategoryNew | None:
        """Категория по турниру"""
        try:
            category = (
                self.session.query(CategoryNew)
                .join(TournamentCategory)
                .filter(
                    TournamentCategory.tournament_id == tournament_id,
                    TournamentCategory.category_id == category_id
                ).first()
            )

            return category
        except Exception as e:
            print(f"Error getting category: {e}")
            return None

    def create_tournament(self, tournament : TournamentNew):
        """Создать турнир"""
        try:
            self.session.add(tournament)
            self.session.commit()
            print(f"Tournament {tournament.name} created with id {tournament.id}")
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error creating tournament {tournament.name}: {e}")
            return False

    def assign_category_tournament(self, category_id, tournament_id, has_consalation = False):
        """Подписать категории к турниру"""
        try:
            category_repo = CategoryRepository()

            exist_category = category_repo.get_category_by_id(category_id)
            if not exist_category:
                print(f"Category with id {category_id} not found")
                raise Exception("Category not found")

            insert_query = (
                insert(TournamentCategory)
                .values(tournament_id=tournament_id, category_id=category_id, has_consolidation_fights=has_consalation)
            )
            self.session.execute(insert_query)
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error assigning category {category_id}: {e}")
            self.session.rollback()
            return False

    def delete_tournament(self, tournament:TournamentNew):
        """Удалить турнир"""
        try:
            self.session.delete(tournament)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error deleting tournament: {e}")
            return False

    def commit_change(self):
        try:
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error committing changes: {e}")
            return False

    def assign_athletes_tournament_after_weighting(self, tournament_category_id, athlete_id):
        try:
            assign_athlete_query = (
                insert(AthleteRegistration)
                .values(tournament_category_id=tournament_category_id, athlete_id=athlete_id)
            )
            self.session.execute(assign_athlete_query)
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error assigning athletes to tournament: {e}")
            self.session.rollback()
            raise e

    def assign_athletes_tournament(self, tournament_id, athlete_id, user_id):
        try:
            athlete_registry = AthleteTournamentRegistration(
                athlete_id = athlete_id,
                tournament_id = tournament_id,
                registered_by = user_id
            )

            self.session.add(athlete_registry)
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error assigning athletes to tournament: {e}")
            self.session.rollback()
            raise e

    def get_tournament_category(self,  tournament_id:int, category_id:int) -> TournamentCategory | None:
        """Получить ID категории турнира"""
        try:
            tournament_category = (
                self.session.query(TournamentCategory)
                .filter_by(tournament_id=tournament_id, category_id=category_id)
                .first()
            )

            if not tournament_category:
                print(f"TournamentCategory not found for tournament_id {tournament_id} and category_id {category_id}")
                return None

            return tournament_category
        except Exception as e:
            print(f"Error getting tournament category id: {e}")
            return None

    def get_tournament_name_by_tournament_category(self, tournament_category_id):
        """Получить турнир по турнир категории"""
        try:
            tournament = (
                self.session.query(TournamentNew.name)
                .join(TournamentCategory, TournamentNew.id == TournamentCategory.tournament_id)
                .filter(
                    TournamentCategory.tournament_category_id == tournament_category_id
                ).scalar()
            )

            if not tournament:
                print(f"Tournament with id {tournament_category_id} not found")
                return None

            return tournament
        except Exception as e:
            print(f"Error getting tournament by id {tournament_category_id}: {e}")
            return None

    def get_tatami_by_tournament(self, tournament_id):
        return self.session.query(TatamiFight).filter_by(tournament_id=tournament_id).all()

    def create_tatami(self, tournament_id,tatami_number):
        try:
            for i in range(tatami_number):
                new_tatami_fight = TatamiFight(
                    tournament_id=tournament_id,
                    tatami_number=i+1
                )

                self.session.add(new_tatami_fight)

            self.session.commit()
        except Exception as e:
            print(f"Error creating tatami: {e}")
            self.session.rollback()

    def unassign_athlete_to_tournament(self, tournament_id, athlete_id):
        try:
            unassign_athlete_query = (
                delete(AthleteTournamentRegistration)
                .where(AthleteTournamentRegistration.tournament_id == tournament_id,
                       AthleteTournamentRegistration.athlete_id == athlete_id)
            )

            self.session.execute(unassign_athlete_query)
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error unassigning athlete to tournament: {e}")
            self.session.rollback()
            raise Exception(f"Error unassigning athlete to tournament: {e}")

    def is_registet_on_tournament(self, tournament_id, athlete_id) -> bool:
        return self.session.query(AthleteTournamentRegistration).filter_by(
            tournament_id=tournament_id,
            athlete_id=athlete_id
        ).first() is not None
