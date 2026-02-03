"""
Генератор турнирных сеток по правилам дзюдо
"""
import math

from database.db import create_session
from new_model.Enums import BracketType
from new_model.head_model.fight_new import FightNew
from repository.athlete_repo import AthleteRepository
from repository.figth_repo import FightRepository
from repository.tournament_repo import TournamentRepository
from services.fight_generator import FightGenerator

tournament_repo = TournamentRepository()
fight_repo = FightRepository()
fight_generator = FightGenerator()

class BracketGenerator:
    """Генератор турнирных сеток"""

    def __init__(self, tournament_id):
        self.session = create_session()
        self.tournament = tournament_repo.get_tournament_by_id(tournament_id)
        self.tournament_id = tournament_id

    def generate_olympic(self, category_id: int):
        try:
            athlete_repo = AthleteRepository()
            athletes = athlete_repo.get_athletes_by_tournament(self.tournament_id, category_id)

            athlete_count = len(athletes)
            if not athletes or athlete_count < 2 or athlete_count == 0:
                raise Exception('No athletes found')

            tournament_category = tournament_repo.get_tournament_category(self.tournament_id, category_id)
            if not tournament_category:
                raise Exception("❌ Tournament category not found")

            # Очищаем существующие схватки
            self.session.query(FightNew).filter_by(tournament_category_id=tournament_category.tournament_category_id).delete()

            # Определяем количество раундов
            total_rounds = self.calculate_rounds(participants_count=athlete_count)

            if total_rounds == 0:
                raise Exception("❌ Invalid number of rounds calculated")

            #распределение участников
            seeded_athletes = self._seed_athletes(athletes)

            fights = self._generate_fights(seeded_athletes, total_rounds, tournament_category.tournament_category_id)
            return fights
        except Exception as e:
            print('Error: ', e)
            return None

    def generate_consolation_by_semifinalists(self, category_id: int):
        try:
            athlete_repo = AthleteRepository()
            athletes = athlete_repo.get_athletes_by_tournament(self.tournament_id, category_id)

            athlete_count = len(athletes)
            if not athletes or athlete_count < 4:
                raise Exception('Not enough athletes for consolation fights')

            tournament_category = tournament_repo.get_tournament_category(self.tournament_id, category_id)
            if not tournament_category:
                raise Exception("❌ Tournament category not found")

            # Определяем количество раундов
            total_rounds = self.calculate_rounds(athlete_count)

            if total_rounds == 0:
                raise Exception("❌ Not enough rounds for consolation fights")

            # Генерация утешительных схваток за 3 место
            consolation_fights = fight_generator.generate_consolation_fights_semifinalist(tournament_category.tournament_category_id,
                                                                            max_rounds=total_rounds)

            return consolation_fights
        except Exception as e:
            print('Error: ', e)
            return None

    def generate_consolation_fights_finalist(self,category_id:int):
        """Генерация утешительных схваток за 3 место между финалистами"""
        try:
            athlete_repo = AthleteRepository()
            athletes = athlete_repo.get_athletes_by_tournament(self.tournament_id, category_id)

            athlete_count = len(athletes)
            if not athletes or athlete_count < 2:
                raise Exception('Not enough athletes for consolation fights')

            tournament_category = tournament_repo.get_tournament_category(self.tournament_id, category_id)
            if not tournament_category:
                raise Exception("❌ Tournament category not found")

            # Определяем количество раундов
            total_rounds = self.calculate_rounds(athlete_count)

            if total_rounds == 0:
                raise Exception("❌ Not enough rounds for consolation fights")

            # Генерация утешительных схваток за 3 место между финалистами
            consolation_fights = fight_generator.generate_consolation_fights_finalist(tournament_category.tournament_category_id,total_rounds)

            return consolation_fights
        except Exception as e:
            print('Error: ', e)
            return None

    def _seed_athletes(self,athletes : list):
        """Посев участников (сильнейшие распределяются)"""

        athlete_count = len(athletes)

        athlete_repo = AthleteRepository()
        # Попытка сортировки по рейтингу (можно добавить логику рейтинга)
        athletes.sort(key=lambda a: athlete_repo.get_victory_count(a.id))

        # Применяем seeding позиции
        positions = self._generate_bracket_positions(athlete_count)
        seeded_athletes = [None] * len(positions)

        for i, pos in enumerate(positions):
            if i < athlete_count:
                seeded_athletes[pos-1] = athletes[i]

        # Убираем None значения (если участников меньше чем позиций)
        return [a for a in seeded_athletes if a is not None]

    def _generate_fights(self, athletes, total_rounds, tournament_category_id, type_bracket=BracketType.MAIN):
        """Генерация схваток для всех раундов"""
        try:
            fights = []
            current_round = 1
            current_athletes = athletes.copy()
            fight_number = 1

            # Генерация первого раунда
            round_fights =  fight_generator.generate_first_round_fights(current_athletes, current_round, fight_number, tournament_category_id, type_bracket)
            fights.extend(round_fights)

            length_fights = len(round_fights)

            # winners для следующего раунда
            current_round_fights = round_fights
            next_fights = [None] * (length_fights // 2)
            fight_number += len(round_fights)
            current_round += 1

            # Генерация последующих раундов
            while current_round <= total_rounds:
                next_round = fight_generator.generate_next_rounds_fights(next_fights,current_round, fight_number, tournament_category_id,type_bracket)

                # Обновляем ссылки на следующие схватки
                for i in range(0, len(current_round_fights), 2):
                    next_fight_index = i // 2

                    # Первый бой из пары
                    if i < len(current_round_fights):
                        fight_repo.update_fight(current_round_fights[i].id,next_round[next_fight_index].id)

                    # Второй бой из пары
                    if i + 1 < len(current_round_fights):
                        fight_repo.update_fight(current_round_fights[i + 1].id,next_round[next_fight_index].id)

                fights.extend(next_round)

                # Обновляем next_athletes для следующего раунда
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
        Работает для любого количества участников ≥ 1.
        """
        if participants_count <= 1:
            return [1]

        # Находим ближайшую степень двойки сверху
        logn = math.ceil(math.log2(participants_count))

        positions = []
        for i in range(participants_count):
            # Инверсия младших logn бит числа i
            rev = 0
            x = i
            for _ in range(logn):
                rev = (rev << 1) | (x & 1)
                x >>= 1
            pos = rev + 1  # переводим в 1-based индекс
            positions.append(pos)

        return positions

    @staticmethod
    def calculate_rounds(participants_count):
        """
        Расчет количества раундов для сетки
        """
        if participants_count <= 0:
            return 0

        return math.ceil(math.log2(participants_count))