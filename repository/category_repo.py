from sqlalchemy import or_

from database.db import get_session
from new_model.handbook.category_new import CategoryNew
from new_model.head_model.new_athlete import AthleteNew
from new_model.head_model.tournament_new import TournamentNew


class CategoryRepository:
    def __init__(self, session=None):
        self.session = session if session else get_session()
        self._owns_session = session is None  # закрывать сессию только если создали сами

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._owns_session:
            return
        if exc_type is not None:
            self.session.rollback()
        self.session.close()

    def add_athlete_to_category(self, athlete: AthleteNew):
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
        """Обновить категорию"""
        try:
            category = self.session.query(CategoryNew).filter_by(id=category_id).first()
            if not category:
                raise Exception("Category not found")

            category.min_weight = category_data.get('min-weight', category.min_weight)
            category.max_weight = category_data.get('max-weight', category.max_weight)
            category.min_age = category_data.get('min-age', category.min_age)
            category.max_age = category_data.get('max-age', category.max_age)
            category.name = category_data.get('name', category.name)

            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error updating category: {e}")
            return False

    def get_categories(self, tournament_id: int):
        query = self.session.query(CategoryNew).filter_by(is_active=True)
        if tournament_id:
            query = query.filter(CategoryNew.tournaments.any(TournamentNew.id == tournament_id))
        return query.all()

    def get_all_athletes(self, category_id):
        try:
            count_athlete = self.session.query(AthleteNew.id).filter(
                CategoryNew.athletes.any(CategoryNew.id == category_id)
            ).count()
            return count_athlete
        except Exception as e:
            print(f"Error getting athletes: {e}")
            return 0

    def create_category(self, category_new: CategoryNew):
        try:
            self.session.add(category_new)
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error creating category: {e}")
            self.session.rollback()
            return False

    def get_category_by_id(self, category_id):
        return self.session.query(CategoryNew).filter_by(id=category_id).first()

    def delete_category(self, category):
        try:
            self.session.delete(category)
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error deleting category: {e}")
            self.session.rollback()
            return False

    def get_id_by_athlete_feature(self, weigth, bith_year, gender):
        category_id = (
            self.session.query(CategoryNew.id)
            .filter(
                CategoryNew.min_weight <= weigth,
                or_(
                    CategoryNew.max_weight >= weigth,
                    CategoryNew.max_weight.is_(None)
                ),
                CategoryNew.min_year <= bith_year,
                CategoryNew.max_year >= bith_year,
                CategoryNew.gender == gender
            ).scalar()
        )
        return category_id

    def get_category_by_name(self, name: str) -> CategoryNew | None:
        return self.session.query(CategoryNew).filter_by(name=name).first()