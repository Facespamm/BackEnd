from database.db import create_session
from models.athlete import Athlete
from models.category import Category


class CategoryRepository:
    def __init__(self):
        self.session = create_session()

    def add_athlete_to_category(self, athlete : Athlete):
        """Добавить участника в категорию"""
        category = (
            self.session.query(Category.id)
            .filter(
                Category.min_weight >= athlete.weight,
                Category.max_weight < athlete.weight,
                Category.min_age >= athlete.age,
                Category.max_age < athlete.age,
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
            category = self.session.query(Category).first(category_id)
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
