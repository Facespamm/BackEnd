"""
Генератор турнирных сеток по правилам дзюдо
"""
import math

from sqlalchemy import delete, select

from database.db import get_session
from new_model.Enums import BracketType
from new_model.head_model.fight_new import FightNew
from new_model.result_new import ResultNew
from new_model.score_event import ScoreEvent
from repository.athlete_repo import AthleteRepository
from repository.figth_repo import FightRepository
from repository.tournament_repo import TournamentRepository
from services.fight_generator import FightGenerator
from utils.helpers import calculate_rounds
from repository.weight_repo import WeightRepository


class BracketGenerator:
    """Генератор турнирных сеток"""

    def __init__(self, tournament_id):
        self.tournament_id = tournament_id
        self.session = get_session()
        self.tournament_repo = TournamentRepository(self.session)
        self.fight_repo = FightRepository(self.session)
        self.fight_generator = FightGenerator(self.session)
        self.tournament = self.tournament_repo.get_tournament_by_id(tournament_id)

    def __del__(self):
        """Закрываем сессию когда объект уничтожается"""
        try:
            self.session.close()
        except Exception:
            pass

    def generate_olympic(self, category_id: int, tatami_number: int):
        try:
            athlete_repo = AthleteRepository(self.session)
            all_athletes = athlete_repo.get_athletes_by_tournament(self.tournament_id, category_id)

            tournament_category = self.tournament_repo.get_tournament_category(self.tournament_id, category_id)
            if not tournament_category:
                raise Exception("❌ Tournament category not found")

            with WeightRepository() as weight_repo:
                athletes = [
                    a for a in all_athletes
                    if any(
                        w.is_valid
                        for w in weight_repo.get_weights(tournament_category.tournament_category_id, a.id) or []
                    )
                ]

            athlete_count = len(athletes)
            if athlete_count < 2:
                raise Exception('Недостаточно атлетов прошедших взвешивание')

            self.init_fight_table(tournament_category.tournament_category_id)

            total_rounds = calculate_rounds(participants_count=athlete_count)
            if total_rounds == 0:
                raise Exception("❌ Invalid number of rounds calculated")

            seeded_athletes = self._seed_athletes(athletes)
            fights = self._generate_fights(
                seeded_athletes,
                total_rounds,
                tournament_category.tournament_category_id,
                tatami_number
            )

            return fights

        except Exception as e:
            print('Error in generate_olympic:', e)
            return None

    def generate_olympic_consolation_fight_semifinal(self, category_id, tatami_number):
        try:
            athlete_repo = AthleteRepository(self.session)
            all_athletes = athlete_repo.get_athletes_by_tournament(self.tournament_id, category_id)

            tournament_category = self.tournament_repo.get_tournament_category(self.tournament_id, category_id)

            with WeightRepository() as weight_repo:
                athletes = [
                    a for a in all_athletes
                    if any(
                        w.is_valid
                        for w in weight_repo.get_weights(tournament_category.tournament_category_id, a.id) or []
                    )
                ]

            athlete_count = len(athletes)
            print(f"athletes after weighing filter: {athlete_count}")

            total_rounds = calculate_rounds(participants_count=athlete_count)
            print(f"total_rounds: {total_rounds}")

            if total_rounds == 0:
                raise Exception("❌ Invalid number of rounds calculated")

            fights = self.fight_generator.generate_consolation_fights_semifinalist(
                tournament_category.tournament_category_id,
                tatami_number,
                total_rounds
            )

            return fights
        except Exception as e:
            print('Error: ', e)
            return None

    def generate_olympic_consolation_fight_final(self, category_id, tatami_number):
        try:
            athlete_repo = AthleteRepository(self.session)
            athletes = athlete_repo.get_athletes_by_tournament(self.tournament_id, category_id)

            athlete_count = len(athletes)
            if not athletes or athlete_count < 2:
                raise Exception('No athletes found')

            tournament_category = self.tournament_repo.get_tournament_category(self.tournament_id, category_id)
            if not tournament_category:
                raise Exception("❌ Tournament category not found")

            total_rounds = calculate_rounds(participants_count=athlete_count)
            if total_rounds == 0:
                raise Exception("❌ Invalid number of rounds calculated")

            fight = self.fight_generator.generate_consolation_fights_finalist(
                tournament_category.tournament_category_id,
                tatami_number,
                total_rounds
            )
            return fight
        except Exception as e:
            print('Error: ', e)
            return None

    def _seed_athletes(self, athletes: list):
        """Посев участников (сильнейшие распределяются)"""
        athlete_count = len(athletes)
        max_athlete = 2 ** math.ceil(math.log2(athlete_count))

        athlete_repo = AthleteRepository(self.session)
        athletes.sort(key=lambda a: athlete_repo.get_victory_count(a.id))

        positions = self._generate_bracket_positions(athlete_count)
        seeded_athletes = [None] * max_athlete

        for i, pos in enumerate(positions):
            if i < athlete_count:
                seeded_athletes[pos - 1] = athletes[i]
            else:
                seeded_athletes[pos - 1] = None

        return [a for a in seeded_athletes]

    def _generate_fights(self, athletes, total_rounds, tournament_category_id, tatami_number, type_bracket=BracketType.MAIN):
        """Генерация схваток для всех раундов"""
        try:
            fights = []
            current_round = 1
            current_athletes = athletes.copy()
            fight_number = 1

            round_fights = self.fight_generator.generate_first_round_fights(
                current_athletes, current_round, fight_number,
                tournament_category_id, tatami_number, type_bracket
            )
            fights.extend(round_fights)

            length_fights = len(round_fights)
            current_round_fights = round_fights
            next_fights = [None] * (length_fights // 2)
            fight_number += len(round_fights)
            current_round += 1

            while current_round <= total_rounds:
                next_round = self.fight_generator.generate_next_rounds_fights(
                    next_fights, current_round, fight_number,
                    tournament_category_id, tatami_number, type_bracket
                )

                for i in range(0, len(current_round_fights), 2):
                    next_fight_index = i // 2
                    if i < len(current_round_fights):
                        self.fight_repo.update_fight(current_round_fights[i].id, next_round[next_fight_index].id)
                    if i + 1 < len(current_round_fights):
                        self.fight_repo.update_fight(current_round_fights[i + 1].id, next_round[next_fight_index].id)

                fights.extend(next_round)
                next_fights = [None] * (len(next_round) // 2)
                current_round_fights = next_round
                fight_number += len(next_round)
                current_round += 1

            return fights
        except Exception as e:
            print("❌ Exception: ", e)

    def _generate_bracket_positions(self, participants_count: int) -> list[int]:
        """
        Генерирует позиции (1-based) для посева участников.
        Использует bit-reversal для равномерного распределения сильнейших.
        """
        if participants_count <= 1:
            return [1]

        logn = math.ceil(math.log2(participants_count))

        positions = []
        for i in range(participants_count):
            rev = 0
            x = i
            for _ in range(logn):
                rev = (rev << 1) | (x & 1)
                x >>= 1
            pos = rev + 1
            positions.append(pos)

        return positions

    def init_fight_table(self, tournament_category_id):
        delete_results = (
            delete(ResultNew)
            .where(ResultNew.fight_id.in_(
                select(FightNew.id).where(
                    FightNew.tournament_category_id == tournament_category_id
                )
            ))
        )
        self.session.execute(delete_results)

        delete_score_event = (
            delete(ScoreEvent)
            .where(ScoreEvent.fight_id.in_(
                select(FightNew.id).where(
                    FightNew.tournament_category_id == tournament_category_id
                )
            ))
        )
        self.session.execute(delete_score_event)

        delete_fight = (
            delete(FightNew)
            .where(FightNew.tournament_category_id == tournament_category_id)
        )
        result = self.session.execute(delete_fight)
        self.session.commit()
        print(f'Delete row in FightNew where tournament_category_id = {tournament_category_id}, count {result}')

    @staticmethod
    def calculate_rounds(athlete_count: int) -> int:
        if athlete_count < 2:
            return 0
        return math.ceil(math.log2(athlete_count))