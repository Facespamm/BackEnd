from database.db import create_session
from new_model.handbook.new_club import ClubNew


class ClubRepository:

    def __init__(self):
        self.session = create_session()

    def get_clubs(self):
        try:
            clubs = self.session.query(ClubNew).filter_by(is_active=True).order_by(ClubNew.name).all()
            return clubs
        except Exception as e:
            print("❌ Exception: ", e)
            return []

    def create_club(self,  data):
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

    def get_club_by_name(self,  name):
        try:
            club = self.session.query(ClubNew).filter_by(name=name.strip(), is_active=True).first()
            return club
        except Exception as e:
            print("❌ Exception: ", e)
            return None