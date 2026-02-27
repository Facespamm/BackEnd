"""
Генератор турнирных сеток по правилам дзюдо
"""
import math

from sqlalchemy import delete, select

from database.db import create_session
from new_model.Enums import BracketType
from new_model.head_model.fight_new import FightNew
from new_model.result_new import ResultNew
from new_model.score_event import ScoreEvent
from repository.athlete_repo import AthleteRepository
from repository.figth_repo import FightRepository
from repository.tournament_repo import TournamentRepository
from services.fight_generator import FightGenerator
from utils.helpers import calculate_rounds

tournament_repo = TournamentRepository()
fight_repo = FightRepository()
fight_generator = FightGenerator(create_session())

class BracketGenerator:
    """Генератор турнирных сеток"""

    def __init__(self, tournament_id):
        self.session = create_session()
        self.tournament = tournament_repo.get_tournament_by_id(tournament_id)
        self.tournament_id = tournament_id

    def generate_olympic(self, category_id: int, tatami_number: int):
        try:
            athlete_repo = AthleteRepository()
            athletes = athlete_repo.get_athletes_by_tournament(self.tournament_id, category_id)

            athlete_count = len(athletes)
            if not athletes or athlete_count < 2 or athlete_count == 0:
                raise Exception('No athletes found')

            tournament_category = tournament_repo.get_tournament_category(self.tournament_id, category_id)
            if not tournament_category:
                raise Exception("❌ Tournament category not found")

            self.init_fight_table(tournament_category.tournament_category_id)

            # Определяем количество раундов
            total_rounds = calculate_rounds(participants_count=athlete_count)

            if total_rounds == 0:
                raise Exception("❌ Invalid number of rounds calculated")

            #распределение участников
            seeded_athletes = self._seed_athletes(athletes)

            fights = self._generate_fights(seeded_athletes, total_rounds, tournament_category.tournament_category_id,tatami_number)
            return fights
        except Exception as e:
            print('Error: ', e)
            return None

    def generate_olympic_consolation_fight_semifinal(self,category_id, tatami_number):
        try:
            athletes = athlete_repo.get_athletes_by_tournament(self.tournament_id, category_id)

            athlete_count = len(athletes)
            if not athletes or athlete_count < 2 or athlete_count == 0:
                raise Exception('No athletes found')

            tournament_category = tournament_repo.get_tournament_category(self.tournament_id, category_id)
            if not tournament_category:
                raise Exception("❌ Tournament category not found")

            total_rounds = calculate_rounds(participants_count=athlete_count)

            if total_rounds == 0:
                raise Exception("❌ Invalid number of rounds calculated")

            session = create_session()
            generator = FightGenerator(session)
            fights = generator.generate_consolation_fights_semifinalist(tournament_category.tournament_category_id,tatami_number,total_rounds)

            for fight in fights:
                fight_repo.create_fight(fight)

            return fights
        except Exception as e:
            print('Error: ', e)
            return None

    def generate_olympic_consolation_fight_final(self,category_id, tatami_number):
        try:
            athletes = athlete_repo.get_athletes_by_tournament(self.tournament_id, category_id)

            athlete_count = len(athletes)
            if not athletes or athlete_count < 2 or athlete_count == 0:
                raise Exception('No athletes found')

            tournament_category = tournament_repo.get_tournament_category(self.tournament_id, category_id)
            if not tournament_category:
                raise Exception("❌ Tournament category not found")

            total_rounds = calculate_rounds(participants_count=athlete_count)

            if total_rounds == 0:
                raise Exception("❌ Invalid number of rounds calculated")

            fight = fight_generator.generate_consolation_fights_finalist(tournament_category.tournament_category_id,tatami_number,total_rounds)
            return fight
        except Exception as e:
            print('Error: ', e)
            return None

    # def generate_consolation_by_semifinalists(self, category_id: int):
    #     try:
    #         athlete_repo = AthleteRepository()
    #         athletes = athlete_repo.get_athletes_by_tournament(self.tournament_id, category_id)
    #
    #         athlete_count = len(athletes)
    #         if not athletes or athlete_count < 4:
    #             raise Exception('Not enough athletes for consolation fights')
    #
    #         tournament_category = tournament_repo.get_tournament_category(self.tournament_id, category_id)
    #         if not tournament_category:
    #             raise Exception("❌ Tournament category not found")
    #
    #         # Определяем количество раундов
    #         total_rounds = self.calculate_rounds(athlete_count)
    #
    #         if total_rounds == 0:
    #             raise Exception("❌ Not enough rounds for consolation fights")
    #
    #         # Генерация утешительных схваток за 3 место
    #         consolation_fights = self.generate_consolation_fights_semifinalist(tournament_category.tournament_category_id,
    #                                                                         max_rounds=total_rounds)
    #
    #         return consolation_fights
    #     except Exception as e:
    #         print('Error: ', e)
    #         return None
    #
    # def generate_consolation_fights_finalist(self,category_id:int):
    #     """Генерация утешительных схваток за 3 место между финалистами"""
    #     try:
    #         athlete_repo = AthleteRepository()
    #         athletes = athlete_repo.get_athletes_by_tournament(self.tournament_id, category_id)
    #
    #         athlete_count = len(athletes)
    #         if not athletes or athlete_count < 2:
    #             raise Exception('Not enough athletes for consolation fights')
    #
    #         tournament_category = tournament_repo.get_tournament_category(self.tournament_id, category_id)
    #         if not tournament_category:
    #             raise Exception("❌ Tournament category not found")
    #
    #         # Определяем количество раундов
    #         total_rounds = self.calculate_rounds(athlete_count)
    #
    #         if total_rounds == 0:
    #             raise Exception("❌ Not enough rounds for consolation fights")
    #
    #         # Генерация утешительных схваток за 3 место между финалистами
    #         consolation_fights = self.generate_consolation_fights_finalist(tournament_category.tournament_category_id,total_rounds)
    #
    #         return consolation_fights
    #     except Exception as e:
    #         print('Error: ', e)
    #         return None

    def _seed_athletes(self,athletes : list):
        """Посев участников (сильнейшие распределяются)"""

        athlete_count = len(athletes)
        max_athlete = 2 ** math.ceil(math.log2(athlete_count))

        # Попытка сортировки по рейтингу (можно добавить логику рейтинга)
        athlete_repo = AthleteRepository()
        athletes.sort(key=lambda a: athlete_repo.get_victory_count(a.id))

        # Применяем seeding позиции
        positions = self._generate_bracket_positions(athlete_count)
        seeded_athletes = [None] * max_athlete

        for i, pos in enumerate(positions):
            if i < athlete_count:
                seeded_athletes[pos-1] = athletes[i]
            else:
                seeded_athletes[pos-1] = None

        # Убираем None значения (если участников меньше чем позиций)
        return [a for a in seeded_athletes]

    def _generate_fights(self, athletes, total_rounds, tournament_category_id, tatami_number, type_bracket=BracketType.MAIN):
        """Генерация схваток для всех раундов"""
        try:
            fights = []
            current_round = 1
            current_athletes = athletes.copy()
            fight_number = 1

            # Генерация первого раунда
            round_fights = fight_generator.generate_first_round_fights(current_athletes, current_round, fight_number, tournament_category_id, tatami_number,type_bracket)
            fights.extend(round_fights)

            length_fights = len(round_fights)

            # winners для следующего раунда
            current_round_fights = round_fights
            next_fights = [None] * (length_fights // 2)
            fight_number += len(round_fights)
            current_round += 1

            # Генерация последующих раундов
            while current_round <= total_rounds:
                next_round = fight_generator.generate_next_rounds_fights(next_fights,current_round, fight_number, tournament_category_id,tatami_number,type_bracket)

                # Обновляем ссылки на следующие схватки
                for i in range(0, len(current_round_fights)):
                    next_fight_index = i

                    # Первый бой из пары
                    if i < len(current_round_fights):
                        fight_repo.update_fight(current_round_fights[i].id,next_round[next_fight_index].id)

                    # # Второй бой из пары
                    # if i + 1 < len(current_round_fights):
                    #     fight_repo.update_fight(current_round_fights[i + 1].id,next_round[next_fight_index].id)

                fights.extend(next_round)

                # Обновляем next_athletes для следующего раунда
                next_fights = [None] * (len(next_round) // 2)
                current_round_fights = next_round
                fight_number += len(next_round)
                current_round += 1

            return fights
        except Exception as e:
            print("❌ Exception: ", e)

    # def _generate_first_round_fights(self,athletes, round_number, start_fight_number, tournament_category_id, tatami_number,type_bracket=BracketType.MAIN):
    #     """Генерация схваток для одного раунда"""
    #     fights = []
    #     fight_number = start_fight_number
    #
    #     athlete_count = len(athletes)
    #     for i in range(0, len(athletes), 2):
    #         white_athlete = athletes[i] if i < athlete_count else None
    #         blue_athlete = athletes[i+1] if i+1 < athlete_count else None
    #
    #         # Пропускаем схватки где оба участника None
    #         if not white_athlete and not blue_athlete:
    #             continue
    #
    #         fight = FightNew(
    #             tournament_category_id=tournament_category_id,
    #             white_athlete_id=white_athlete.id if white_athlete else None,
    #             blue_athlete_id=blue_athlete.id if blue_athlete else None,
    #             round_number=round_number,
    #             fight_number=fight_number,
    #             status=FightStatus.SCHEDULED,
    #             type_bracket = type_bracket,
    #             tatami_number = tatami_number,
    #         )
    #
    #         #сохроняем бой
    #         fight_repo.create_fight(fight)
    #
    #         fights.append(fight)
    #         fight_number += 1
    #
    #     return fights
    #
    # def _generate_next_rounds_fights(self,next_fight,round_number, next_fight_number, tournament_category_id, tatami_number,type_bracket=BracketType.MAIN):
    #     """Генерация схваток для следующих раунда"""
    #     fights = []
    #     fight_number = next_fight_number
    #
    #     length_next_fight = len(next_fight)
    #     for i in range(length_next_fight):
    #         fight = FightNew(
    #             tournament_category_id=tournament_category_id,
    #             white_athlete_id=None,
    #             blue_athlete_id=None,
    #             round_number=round_number,
    #             fight_number=fight_number,
    #             status=FightStatus.SCHEDULED,
    #             type_bracket=type_bracket,
    #             tatami_number = tatami_number,
    #         )
    #
    #         # сохроняем бой
    #         fight_repo.create_fight(fight)
    #
    #         fights.append(fight)
    #         fight_number += 1
    #
    #     return  fights

    # def _generate_consolation_fights_semifinalist(self, tournament_category_id, max_rounds):
    #     """Генерация утешительных схваток за 3 место"""
    #     # Находим полуфиналистов которые проиграли
    #
    #     semi_fights = fight_repo.get_semi_final_fights(tournament_category_id, max_rounds-1)
    #
    #     semifinal_fights = [f for f in semi_fights]
    #     if len(semifinal_fights) < 2:
    #         raise Exception("❌ Недостаточно полуфиналистов для утешительных боев")
    #
    #     result_repo = ResultRepository()
    #
    #     # Схватка за 3 место между проигравшими в полуфиналах
    #     losers = []
    #     for fight in semifinal_fights:
    #         loser = result_repo.get_loser(fight.id)
    #         if loser:
    #             losers.append(loser)
    #
    #     length_losers = len(losers)
    #
    #     if not length_losers or length_losers <2:
    #         raise Exception('❌ No losers found for consolation fights')
    #
    #     total_rounds = max_rounds-1
    #     consolation_fights = self._generate_fights(losers,total_rounds,tournament_category_id,BracketType.Consolation_by_Semifinalists)
    #
    #     return consolation_fights
    #
    # def _generate_consolation_fights_finalist(self, tournament_category_id, max_rounds):
    #     """Генерация утешительных схваток за 3 место"""
    #     # Находим полуфиналистов которые проиграли
    #
    #     final_fights = fight_repo.get_final_fights(tournament_category_id, max_rounds)
    #
    #     semifinal_fights = [f for f in final_fights]
    #     if len(semifinal_fights) != 2:
    #         raise Exception("❌ Недостаточно боев для утешительных боев")
    #
    #     result_repo = ResultRepository()
    #     # Схватка за 3 место между проигравшими в полуфиналах
    #     losers = []
    #     for fight in semifinal_fights:
    #         loser = result_repo.get_loser(fight.id)
    #         if loser:
    #             losers.append(loser)
    #
    #     length_losers = len(losers)
    #
    #     if not length_losers or length_losers <2:
    #         raise Exception('❌ No losers found for consolation fights')
    #
    #     total_rounds = max_rounds-1
    #     consolation_fights = self._generate_fights(losers,total_rounds,tournament_category_id,BracketType.Consolation_by_Finalists)
    #
    #     return consolation_fights

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

        # Очищаем существующие схватки
        delete_figh = (
            delete(FightNew)
            .where(FightNew.tournament_category_id == tournament_category_id)
        )
        result = self.session.execute(delete_figh)
        self.session.commit()
        print(f'Delete row in FightNew where tournament_category_id = {tournament_category_id}, count {result}')