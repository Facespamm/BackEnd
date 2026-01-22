from sqlalchemy import true, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.sql.functions import count

from database.db import create_session
from new_model.handbook.category_new import CategoryNew
from new_model.head_model.tournament_new import TournamentNew
from new_model.new_associations import tournament_categories, athlete_tournament


class TournamentRepository:
    def __init__(self):
        self.session = create_session()

    # TODO Переделать под новые модели
    # def add_club_to_tournament(self,  tournament_id, club_id):
    #     """Добавить клуб к турниру"""
    #     try:
    #         tournament = self.session.query(TournamentNew).filter_by(id=tournament_id).first()
    #         if not tournament:
    #             print(f"Tournament with id {tournament_id} not found")
    #             raise Exception("Tournament not found")
    #
    #         #categories = self.session.query(Category).filter_by(tournament_id=tournament.id).all()
    #
    #         #category_ids = [cat.id for cat in categories]
    #         #if not category_ids:
    #         #    print(f"No categories found for tournament {tournament_id}")
    #         #    return False
    #
    #         #query = (
    #         #    select(Athlete)
    #         #    .join(category_athletes, Athlete.id == category_athletes.c.athlete_id)
    #         #    .where(category_athletes.c.category_id.in_(category_ids),
    #         #           Athlete.club_id == club_id,
    #         #           Athlete.is_active == True)
    #         #)
    #
    #         #athletes =  self.session.execute(query).scalars().all()
    #
    #         athletes = self.session.query(Athlete).filter_by(club_id=club_id, is_active = True).all()
    #
    #         if not athletes:
    #             print(f"No eligible athletes found for club {club_id}")
    #
    #         for athlete in athletes:
    #             if athlete not in tournament.athletes:
    #                 tournament.athletes.append(athlete)
    #
    #         self.session.commit()
    #         print(f"Added {len(athletes)} athletes from club {club_id} to tournament {tournament_id}")
    #     except Exception as e:
    #         self.session.rollback()
    #         print(f"Error adding club {club_id} to tournament {tournament_id}")
    #         raise
    #
    # def get_tournament_categories(self, tournament_id):
    #     """Получить категории турнира"""
    #     try:
    #         tournament = self.session.query(Tournament).filter_by(id=tournament_id).first()
    #         if not tournament:
    #             print(f"Tournament with id {tournament_id} not found")
    #             raise Exception("Tournament not found")
    #
    #         categories = self.session.query(Category).filter_by(tournament_id=tournament.id).all()
    #         return categories
    #     except Exception as e:
    #         print(f"Error getting categories for tournament {tournament_id}: {e}")
    #         return []
    #
    # def add_athlete_to_tournament(self, tournament_id, athlete_id):
    #     """Добавить участника к турниру"""
    #     try:
    #         tournament = self.session.query(Tournament).filter_by(id=tournament_id).first()
    #         athlete = self.session.query(Athlete).filter_by(id=athlete_id).first()
    #
    #         if not tournament:
    #             print(f"Tournament with id {tournament_id} not found")
    #             raise Exception("Tournament not found")
    #
    #         if not athlete:
    #             print(f"Athlete with id {athlete_id} not found")
    #             raise Exception("Athlete not found")
    #
    #         if athlete in tournament.athletes:
    #             print(f"Athlete {athlete_id} already registered for tournament {tournament_id}")
    #             return False
    #
    #         #categories = self.get_tournament_categories(tournament_id)
    #         #athlete_categories = [
    #         #    category for category in categories if athlete in category.athletes
    #         #]
    #
    #         #if not athlete_categories:
    #         #    print(f"Athlete {athlete_id} does not belong to any category in tournament {tournament_id}")
    #         #    return False
    #
    #         tournament.athletes.append(athlete)
    #         self.session.commit()
    #         print(f"Athlete {athlete_id} added to tournament {tournament_id}")
    #         return True
    #     except Exception as e:
    #         self.session.rollback()
    #         print(f"Error adding athlete {athlete_id} to tournament {tournament_id}: {e}")
    #         return False

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
                self.session.query(count(athlete_tournament.c.athlete_id))
                .filter(
                    athlete_tournament.c.tournament_id == tournament_id
                ).scalar()
            )

            return count_athlete if count_athlete else 0
        except Exception as e:
            print(f"Error getting athlete count: {e}")
            return None

    def get_category(self, tournament_id):
        """Категория"""
        try:
            category = (
                self.session.query(CategoryNew)
                .join(tournament_categories)
                .filter(tournament_categories.c.tournament_id == tournament_id)
                .all()
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

    def assign_category_tournament(self, category_id, tournament_id):
        """Подписать категории к турниру"""
        try:
            insert_query = (
                insert(tournament_categories)
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