from sqlalchemy import select

from databse.db import create_session
from models.associations import category_athletes
from models.athlete import Athlete
from models.category import Category
from models.tournament import Tournament


class TournamentRepository:
    def __init__(self):
        self.session = create_session()

    def add_club_to_tournament(self,  tournament_id, club_id):
        """Добавить клуб к турниру"""
        try:
            tournament = self.session.query(Tournament).filter_by(id=tournament_id).first()
            if not tournament:
                print(f"Tournament with id {tournament_id} not found")
                raise Exception("Tournament not found")

            categories = self.session.query(Category).filter_by(tournament_id=tournament.id).all()

            category_ids = [cat.id for cat in categories]
            if not category_ids:
                print(f"No categories found for tournament {tournament_id}")
                return False

            query = (
                select(Athlete)
                .join(category_athletes, Athlete.id == category_athletes.c.athlete_id)
                .where(category_athletes.c.category_id.in_(category_ids),
                       Athlete.club_id == club_id,
                       Athlete.is_active == True)
            )

            athletes =  self.session.execute(query).scalars().all()

            if not athletes:
                print(f"No eligible athletes found for club {club_id}")

            for athlete in athletes:
                if athlete not in tournament.athletes:
                    tournament.athletes.append(athlete)

            self.session.commit()
            print(f"Added {len(athletes)} athletes from club {club_id} to tournament {tournament_id}")
        except Exception as e:
            self.session.rollback()
            print(f"Error adding club {club_id} to tournament {tournament_id}")
            raise

    def get_tournament_categories(self, tournament_id):
        """Получить категории турнира"""
        try:
            tournament = self.session.query(Tournament).filter_by(id=tournament_id).first()
            if not tournament:
                print(f"Tournament with id {tournament_id} not found")
                raise Exception("Tournament not found")

            categories = self.session.query(Category).filter_by(tournament_id=tournament.id).all()
            return categories
        except Exception as e:
            print(f"Error getting categories for tournament {tournament_id}: {e}")
            return []

    def add_athlete_to_tournament(self, tournament_id, athlete_id):
        """Добавить участника к турниру"""
        try:
            tournament = self.session.query(Tournament).filter_by(id=tournament_id).first()
            athlete = self.session.query(Athlete).filter_by(id=athlete_id).first()

            if not tournament:
                print(f"Tournament with id {tournament_id} not found")
                raise Exception("Tournament not found")

            if not athlete:
                print(f"Athlete with id {athlete_id} not found")
                raise Exception("Athlete not found")

            if athlete in tournament.athletes:
                print(f"Athlete {athlete_id} already registered for tournament {tournament_id}")
                return False

            categories = self.get_tournament_categories(tournament_id)
            athlete_categories = [
                category for category in categories if athlete in category.athletes
            ]

            if not athlete_categories:
                print(f"Athlete {athlete_id} does not belong to any category in tournament {tournament_id}")
                return False

            tournament.athletes.append(athlete)
            self.session.commit()
            print(f"Athlete {athlete_id} added to tournament {tournament_id}")
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error adding athlete {athlete_id} to tournament {tournament_id}: {e}")
            return False