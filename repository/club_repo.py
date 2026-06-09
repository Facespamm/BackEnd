from database.db import get_session
from models.new_club import ClubNew
from routers.club.schemas import CreateClubRequest


class ClubRepository:
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

    def get_clubs(self):
        try:
            return (
                self.session.query(ClubNew)
                .filter_by(is_active=True)
                .order_by(ClubNew.name)
                .all()
            )
        except Exception as e:
            print("❌ Exception: ", e)
            return []

    def create_club(self, club_data: CreateClubRequest):
        try:
            club_new = ClubNew(
                name=club_data.name,
                short_name=club_data.short_name,
                city=club_data.city,
                country=club_data.country,
                address=club_data.address,
                phone=club_data.phone,
                email=club_data.email,
                website=club_data.website,
                coach_name=club_data.coach_name,
                founded_year=club_data.founded_year,
            )
            self.session.add(club_new)
            self.session.commit()
            return True
        except Exception as e:
            print("❌ Exception: ", e)
            self.session.rollback()
            return False

    def delete_club(self, club_id: int) -> bool:
        from models.new_athlete import AthleteNew

        try:
            club = self.session.query(ClubNew).filter_by(id=club_id).first()
            if not club:
                return False
            self.session.query(AthleteNew).filter(AthleteNew.club_id == club_id).update(
                {AthleteNew.club_id: None}, synchronize_session=False
            )
            self.session.delete(club)
            self.session.commit()
            return True
        except Exception as e:
            print(f"❌ Exception in delete_club: {e}")
            self.session.rollback()
            return False

    def update_club(self, club_id: int, update_data: dict) -> bool:
        try:
            club = (
                self.session.query(ClubNew)
                .filter_by(id=club_id, is_active=True)
                .first()
            )
            if not club:
                return False
            for key, value in update_data.items():
                if hasattr(club, key):
                    setattr(
                        club, key, value.strip() if isinstance(value, str) else value
                    )
            self.session.commit()
            return True
        except Exception as e:
            print("❌ Exception in update_club: ", e)
            self.session.rollback()
            return False

    def get_club_by_name(self, name):
        try:
            return (
                self.session.query(ClubNew)
                .filter_by(name=name.strip(), is_active=True)
                .first()
            )
        except Exception as e:
            print("❌ Exception: ", e)
            return None

    def get_athletes_by_club(self, club_id: int):
        from models.new_athlete import AthleteNew

        try:
            return (
                self.session.query(AthleteNew)
                .filter_by(club_id=club_id, is_active=True)
                .all()
            )
        except Exception as e:
            print("❌ Exception: ", e)
            return []

    def _get_athletes_id_by_club(self, club_id: int):
        from models.new_athlete import AthleteNew

        try:
            return (
                self.session.query(AthleteNew.id)
                .filter_by(club_id=club_id, is_active=True)
                .all()
            )
        except Exception as e:
            print("❌ Exception: ", e)
            return []

    def get_club_by_id(self, club_id: int):
        try:
            return (
                self.session.query(ClubNew)
                .filter_by(id=club_id, is_active=True)
                .first()
            )
        except Exception as e:
            print("❌ Exception: ", e)
            return None

    def assign_athlete_to_club(self, club_id: int, athlete_ids: list[int]) -> bool:
        try:
            existing_athlete = self._get_athletes_id_by_club(club_id)
            ignore_existing_athlete = [
                a for a in athlete_ids if a not in existing_athlete
            ]

            from models.new_athlete import AthleteNew

            for athlete_id in ignore_existing_athlete:
                athlete = (
                    self.session.query(AthleteNew).filter_by(id=athlete_id).first()
                )
                if not athlete:
                    continue

                athlete.club_id = club_id

            self.session.commit()
            return True
        except Exception as e:
            print("Exception in assign_athlete_to_club: ", e)
            self.session.rollback()
            raise e

    def unassign_athletes_from_club(self, club_id: int, athlete_ids: list[int]):
        try:
            existing_athlete = self._get_athletes_id_by_club(club_id)
            has_athlete = [a for a in athlete_ids if a not in existing_athlete]
            if not has_athlete:
                raise Exception("athlete not found this club")

            from models.new_athlete import AthleteNew

            for athlete_id in has_athlete:
                athlete = (
                    self.session.query(AthleteNew).filter_by(id=athlete_id).first()
                )
                if not athlete:
                    continue

                athlete.club_id = None

            self.session.commit()
            return True
        except Exception as e:
            print("Exception in assign_athlete_to_club: ", e)
            self.session.rollback()
            raise e
