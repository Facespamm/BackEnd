from sqlalchemy import true, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.sql.functions import count

from api.categories import category_repo
from database.db import create_session
from new_model.handbook.category_new import CategoryNew
from new_model.head_model.new_athlete import AthleteNew
from new_model.head_model.tournament_new import TournamentNew
from new_model.new_associations import TournamentCategory, AthleteRegistration


class TournamentRepository:
    def __init__(self):
        self.session = create_session()

    # def add_club_to_tournament(self,  tournament_id, club_id):
    #     """Добавить клуб к турниру"""
    #     try:
    #         tournament = self.get_tournament_by_id(tournament_id)
    #         if not tournament:
    #             print(f"Tournament with id {tournament_id} not found")
    #             raise Exception("Tournament not found")
    #
    #         categories = self.get_category(tournament.id)
    #
    #         category_ids = [cat.id for cat in categories]
    #         if not category_ids:
    #             print(f"No categories found for tournament {tournament_id}")
    #             return False
    #
    #         athletes = (
    #             self.session.query(AthleteNew)
    #             .filter(AthleteNew.category_id.in_(category_ids),
    #                    AthleteNew.club_id == club_id,
    #                    )
    #             .all()
    #         )
    #
    #         # Все атлеты по клюбу
    #         # athletes = self.session.query(Athlete).filter_by(club_id=club_id, is_active = True).all()
    #
    #         if not athletes:
    #             print(f"No eligible athletes found for club {club_id}")
    #             raise
    #
    #         tournament_categoryies= (
    #             self.session.query(tournament_categories)
    #             .filter(
    #                 tournament_categories.c.category_id.in_(category_ids),
    #                 tournament_categories.c.tournament_id == tournament_id,
    #             )
    #             .all()
    #         )
    #
    #         existing_assign_athletes = (
    #             self.session.query(athlete_tournament.c.athlete_id)
    #             .filter(
    #                 athlete_tournament.c.tournament_category_id.in_(tournament_categoryies)
    #             )
    #             .all()
    #         )
    #
    #         for athlete in athletes:
    #             if athlete.id not in existing_assign_athletes:
    #                 tournament_category_id = [id for id in tournament_categoryies if id.c.category_id == athlete.category_id]
    #                 if not tournament_category_id:
    #                     continue
    #                 self.assign_athletes_tournament(tournament_category_id[0], athlete.id)
    #
    #         print(f"Added {len(athletes)} athletes from club {club_id} to tournament {tournament_id}")
    #     except Exception as e:
    #         self.session.rollback()
    #         print(f"Error adding club {club_id} to tournament {tournament_id}")
    #         raise

    def add_club_to_tournament(self, tournament_id, club_id):
        """Добавить клуб к турниру"""
        try:
            tournament = self.get_tournament_by_id(tournament_id)
            if not tournament:
                raise ValueError(f"Tournament with id {tournament_id} not found")

            categories = self.get_category(tournament.id)
            category_ids = [cat.id for cat in categories]

            if not category_ids:
                raise ValueError(f"No categories found for tournament {tournament_id}")

            # Получаем атлетов клуба в нужных категориях
            athletes = (
                self.session.query(AthleteNew)
                .filter(
                    AthleteNew.category_id.in_(category_ids),
                    AthleteNew.club_id == club_id
                )
                .all()
            )

            if not athletes:
                raise ValueError(f"No eligible athletes found for club {club_id}")

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
            tc_by_category = {tc.category_id: tc.id for tc in tournament_category_records}

            # Получаем уже назначенных атлетов
            existing_athlete_ids = {
                row[0] for row in
                self.session.query(AthleteRegistration.athlete_id)
                .filter(AthleteRegistration.tournament_category_id.in_(tc_ids))
                .all()
            }

            # Назначаем новых атлетов
            added_count = 0
            for athlete in athletes:
                if athlete.id in existing_athlete_ids:
                    continue

                tournament_category_id = tc_by_category.get(athlete.category_id)
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

            if athlete in tournament.athletes:
                print(f"Athlete {athlete_id} already registered for tournament {tournament_id}")
                return False

            categories = self.get_category(tournament_id,category_id)
            athlete_categories = [category for category in categories if athlete in category.athletes]

            if not athlete_categories:
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


            print(f"Athlete {athlete_id} added to tournament {tournament_id} with category {category_id}")
            return self.assign_athletes_tournament(tournament_category_id, athlete_id)
        except Exception as e:
            self.session.rollback()
            print(f"Error adding athlete {athlete_id} to tournament {tournament_id}: {e}")
            return False

    def get_tournament_by_id(self, tournament_id):
        """Получить турнир по ID"""
        try:
            tournament = self.session.query(TournamentNew).filter_by(id=tournament_id).one_or_none()

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
            #TODO надо добавить поля is_active в турниры
            # tournaments_query = self.session.query(TournamentNew).filter_by(is_active = True).order_by(TournamentNew.start_date.desc())
            tournaments_query = self.session.query(TournamentNew).order_by(TournamentNew.start_date.desc())

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

    def get_category(self, tournament_id, category_id = None):
        """Категория"""
        try:
            category = (
                self.session.query(CategoryNew)
                .join(TournamentCategory)
                .filter(TournamentCategory.tournament_id == tournament_id)
            )

            if category_id:
                category = category.filter(TournamentCategory.category_id == category_id).first()
                return category

            return category.all()
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

    def assign_category_tournament(self, category_id, tournament_id):
        """Подписать категории к турниру"""
        try:
            insert_query = (
                insert(TournamentCategory)
                .values(tournament_id=tournament_id, category_id=category_id)
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

    def get_tournament_category_id(self,  tournament_id:int, category_id:int):
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

            return tournament_category.tournament_category_id
        except Exception as e:
            print(f"Error getting tournament category id: {e}")
            return None