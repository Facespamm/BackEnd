from database.db import get_session
from new_model.handbook.new_club import ClubNew


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
            return self.session.query(ClubNew).filter_by(is_active=True).order_by(ClubNew.name).all()
        except Exception as e:
            print("❌ Exception: ", e)
            return []

    def create_club(self, data):
        try:
            club_new = ClubNew(
                name=data['name'].strip(),
                short_name=data.get('short_name'),
                city=data.get('city'),
                country=data.get('country', 'Россия'),
                address=data.get('address'),
                phone=data.get('phone'),
                email=data.get('email'),
                website=data.get('website'),
                coach_name=data.get('coach_name'),
                founded_year=data.get('founded_year')
            )
            self.session.add(club_new)
            self.session.commit()
            return True
        except Exception as e:
            print("❌ Exception: ", e)
            self.session.rollback()
            return False

    def delete_club(self, club_id: int) -> bool:
        from new_model.head_model.new_athlete import AthleteNew
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
            club = self.session.query(ClubNew).filter_by(id=club_id, is_active=True).first()
            if not club:
                return False
            for key, value in update_data.items():
                if hasattr(club, key):
                    setattr(club, key, value.strip() if isinstance(value, str) else value)
            self.session.commit()
            return True
        except Exception as e:
            print("❌ Exception in update_club: ", e)
            self.session.rollback()
            return False

    def get_club_by_name(self, name):
        try:
            return self.session.query(ClubNew).filter_by(name=name.strip(), is_active=True).first()
        except Exception as e:
            print("❌ Exception: ", e)
            return None

    def get_athletes_by_club(self, club_id: int):
        from new_model.head_model.new_athlete import AthleteNew
        try:
            return self.session.query(AthleteNew).filter_by(club_id=club_id, is_active=True).all()
        except Exception as e:
            print("❌ Exception: ", e)
            return []

    def get_club_by_id(self, club_id: int):
        try:
            return self.session.query(ClubNew).filter_by(id=club_id, is_active=True).first()
        except Exception as e:
            print("❌ Exception: ", e)
            return None