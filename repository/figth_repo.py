from sqlalchemy import select, update, insert, delete

from database.db import create_session
from new_model.head_model.fight_new import FightNew
from new_model.new_associations import fight_referee
from repository.tournament_repo import TournamentRepository


class FightRepository:
    def __init__(self):
        self.session = create_session()

    def assign_referee(self, referee_id, fight_id ,role):
        """Назначить судью на бой"""
        # Проверяем, не назначен ли уже судья на эту роль
        existing_query = (
            select(fight_referee)
            .where(fight_referee.c.fight_id == fight_id)
            .where(fight_referee.c.role == role)
        )
        existing = self.session.execute(existing_query).first()

        if existing:
            # Обновляем существующую запись
            update_query = (
                update(fight_referee)
                .where(fight_referee.c.fight_id == fight_id)
                .where(fight_referee.c.role == role)
                .values(referee_id=referee_id)
            )
            self.session.execute(update_query)
        else:
            # Добавляем новую запись
            insert_query = (
                insert(fight_referee)
                .values(
                    fight_id=fight_id,
                    referee_id=referee_id,
                    role=role
                )
            )
            self.session.execute(insert_query)
        self.session.commit()

    def remove_referee(self, fight_id,role):
        """Убрать судью с определенной роли"""
        delete_query = (
            delete(fight_referee)
            .where(fight_referee.c.fight_id == fight_id)
            .where(fight_referee.c.role == role)
        )
        self.session.execute(delete_query)
        self.session.commit()

    def create_fight(self, fight):
        self.session.add(fight)
        self.session.commit()

    def get_fight_by_tournament(self, tournament_id):
        return self.session.query(FightNew).filter_by(tournament_id = tournament_id).all()