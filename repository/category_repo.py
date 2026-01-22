from sqlalchemy.sql.functions import count

from database.db import create_session
from new_model.handbook.category_new import CategoryNew
from new_model.head_model.new_athlete import AthleteNew
from new_model.head_model.tournament_new import TournamentNew
from new_model.new_associations import new_category_athletes


class CategoryRepository:
    def __init__(self):
        self.session = create_session()

    def add_athlete_to_category(self, athlete : AthleteNew):
        """Добавить участника в категорию"""
        category = (
            self.session.query(CategoryNew)
            .filter(
                CategoryNew.min_weight >= athlete.weight,
                CategoryNew.max_weight < athlete.weight,
                CategoryNew.min_age >= athlete.age,
                CategoryNew.max_age < athlete.age,
            ).first()
        )

        if category:
            category.athletes.append(athlete)
            self.session.commit()
            return True

        return False

    def update_category(self, category_id, category_data: dict):
        """Создать новую категорию"""
        try:
            category = self.session.query(CategoryNew).first(category_id)
            if not category:
                raise Exception("Category not found")

            category.min_weight = category_data.get('min-weight',category.min_weight)
            category.max_weight = category_data.get('max-weight',category.max_weight)
            category.min_age = category_data.get('min-age',category.min_age)
            category.max_age = category_data.get('max-age',category.max_age)
            category.name = category_data.get('name',category.name)

            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error updating category: {e}")
            return False

    def get_categories(self, tournament_id:int):
        query = self.session.query(CategoryNew).filter_by(is_active=True)
        if tournament_id:
            query = query.filter(CategoryNew.tournaments.any(TournamentNew.id == tournament_id))
        return query.all()

    #TODO доделать
    def get_all_athletes(self):
        query = (
            self.session.query(count(new_category_athletes.c.athlete_id))
        )