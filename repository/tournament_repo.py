from sqlalchemy import and_, extract
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.functions import count

from database.db import get_session
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
        """Добавить клуб к турниру"""
        try:
            tournament = self.get_tournament_by_id(tournament_id)
            if not tournament:
                raise ValueError(f"Tournament with id {tournament_id} not found")

            categories = self.get_categories(tournament.id)
            category_ids = [cat.id for cat in categories]

            if not category_ids:
                raise ValueError(f"No categories found for tournament {tournament_id}")

            # Получаем атлетов клуба в нужных категориях
            athletes = (
                self.session.query(AthleteNew,CategoryNew.id.label('category_id'))
                .join(
                    CategoryNew,
                    and_(
                        CategoryNew.id.in_(category_ids),
                        extract('year', AthleteNew.birth_date) >= CategoryNew.min_year,
                        extract('year', AthleteNew.birth_date) <= CategoryNew.max_year
                    )
                )
                .all()
            )

            if not athletes:
                raise ValueError(f"Не найдено ни одного подходящего спортсмена для регистрации на турнир по данным категориям"
                                 f" {club_id}")

            # Получаем ID связей турнир-категория
            tournament_category_records = (
                self.session.query(TournamentCategory)
                .filter(
                    TournamentCategory.category_id.in_(category_ids),
                    TournamentCategory.tournament_id == tournament_id
                )
                .all()
            )

            tc_ids = [tc.tournament_category_id for tc in tournament_category_records]
            tc_by_category = { tc.category_id : tc.tournament_category_id for tc in tournament_category_records}

            # Получаем уже назначенных атлетов
            existing_athlete_ids = {
                row[0] for row in
                self.session.query(AthleteRegistration.athlete_id)
                .filter(AthleteRegistration.tournament_category_id.in_(tc_ids))
                .all()
            }

            # Назначаем новых атлетов
            added_count = 0
            for athlete, category_id  in athletes:
                if athlete.id in existing_athlete_ids:
                    continue

                tournament_category_id = tc_by_category.get(category_id)
                if not tournament_category_id:
                    continue

                self.assign_athletes_tournament(tournament_category_id, athlete.id)
                added_count += 1

            print(f"Added {added_count} athletes from club {club_id} to tournament {tournament_id}")
            return True

        except Exception as e:
            self.session.rollback()
            print(f"Error adding club {club_id} to tournament {tournament_id}: {e}")
            raise

    def get_tournament_athletes(self, tournament_id, category_id=None):
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


    def add_athlete_to_tournament(self, tournament_id, category_id, athlete_id):
        """Добавить участника к турниру"""
        try:
            tournament = self.get_tournament_by_id(tournament_id)

            athlete = self.session.query(AthleteNew).filter_by(id=athlete_id).first()

            if not tournament:
                print(f"Tournament with id {tournament_id} not found")
                raise Exception("Tournament not found")

            if not athlete:
                print(f"Athlete with id {athlete_id} not found")
                raise Exception("Athlete not found")

            category = self.get_category(tournament_id,category_id)
            athlete_category = category.min_year <= athlete.birth_date.year <= category.max_year

            if not athlete_category:
               print(f"Athlete {athlete_id} does not belong to any category in tournament {tournament_id}")
               return False

            tournament_category_id = (
                self.session.query(TournamentCategory.tournament_category_id)
                .filter(
                    TournamentCategory.category_id == category_id,
                    TournamentCategory.tournament_id == tournament_id,
                )
                .scalar()
            )

            athlete_registry = (
                self.session.query(AthleteRegistration.athlete_id)
                .filter(
                    AthleteRegistration.tournament_category_id == tournament_category_id,
                )
                .all()
            )

            if athlete.id in athlete_registry:
                print(f"Athlete {athlete_id} already registered for tournament {tournament_id}")
                return False

            print(f"Athlete {athlete_id} added to tournament {tournament_id} with category {category_id}")
            return self.assign_athletes_tournament(tournament_category_id, athlete_id)
        except Exception as e:
            self.session.rollback()
            print(f"Error adding athlete {athlete_id} to tournament {tournament_id}: {e}")
            return False

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

    def assign_athletes_tournament(self, tournament_category_id, athlete_id):
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
            return False

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