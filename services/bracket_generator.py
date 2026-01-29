"""
Генератор турнирных сеток по правилам дзюдо
"""
import math
import random

from database.db import create_session
from new_model.Enums import FightStatus
from new_model.head_model.fight_new import FightNew
from repository.athlete_repo import AthleteRepository
from repository.figth_repo import FightRepository
from repository.result_repo import ResultRepository
from repository.tournament_repo import TournamentRepository

tournament_repo = TournamentRepository()

class BracketGenerator:
    """Генератор турнирных сеток"""

    def __init__(self, tournament_id):
        self.session = create_session()
        self.tournament = tournament_repo.get_tournament_by_id(tournament_id)
        self.tournament_id = tournament_id

    def generate(self, category_id: int):
        """Генерация сетки по олимпийской системе"""
        try:
            athlete_repo = AthleteRepository()
            athletes = athlete_repo.get_athletes_by_tournament(self.tournament_id, category_id)

            if not athletes:
                return []

            athletes_count = len(athletes)
            if athletes_count < 2:
                return []

            tournament_category_id = tournament_repo.get_tournament_category_id(self.tournament_id, category_id)
            if not tournament_category_id:
                print("❌ Tournament category not found")
                return []
            # Очищаем существующие схватки
            self.session.query(FightNew).filter_by(tournament_category_id=tournament_category_id).delete()

            # Определяем количество раундов
            total_rounds = self._calculate_rounds(athletes_count)

            if athletes_count == 0:
                return False

            # Seed участников (сильнейшие не встречаются в первых раундах)
            seeded_athletes = self._seed_athletes(athletes)

            # Генерируем схватки
            self._generate_fights(seeded_athletes, total_rounds, tournament_category_id)
            return True
        except Exception as e:
            print("❌ Exception: ", e)
            return False

    def _seed_athletes(self,athletes : list):
        """Посев участников (сильнейшие распределяются)"""

        athlete_count = len(athletes)
        # Сортируем по рейтингу (если есть) или случайно
        try:
            athlete_repo = AthleteRepository()
            # Попытка сортировки по рейтингу (можно добавить логику рейтинга)
            athletes.sort(key=lambda a: athlete_repo.get_victory_count(a), reverse=True)
        except Exception as e:
            # Случайное перемешивание если нет данных
            random.shuffle(athletes)
            print("Ошибка при сортировке по рейтингу, используется случайное перемешивание:", e)

        # Применяем seeding позиции
        positions = self._generate_bracket_positions(athlete_count)
        seeded_athletes = [None] * len(positions)

        for i, pos in enumerate(positions):
            if i < len(athletes):
                seeded_athletes[pos-1] = athletes[i]

        # Убираем None значения (если участников меньше чем позиций)
        return [a for a in seeded_athletes if a is not None]

    def _generate_fights(self, athletes, total_rounds, tournament_category_id):
        """Генерация схваток для всех раундов"""
        try:
            fights = []
            current_round = total_rounds
            current_athletes = athletes.copy()
            fight_number = 1

            # Генерация первого раунда
            round_fights = self._generate_round_fights(current_athletes, current_round, fight_number, tournament_category_id)
            fights.extend(round_fights)

            # winners для следующего раунда
            next_athletes = [None] * len(fights)
            fight_number += len(round_fights)
            current_round -= 1

            # Генерация последующих раундов
            while current_round > 0:
                round_fights = self._generate_round_fights(next_athletes, current_round, fight_number, tournament_category_id)
                fights.extend(round_fights)

                # Обновляем next_athletes для следующего раунда
                next_athletes = [None] * (len(round_fights) // 2)
                fight_number += len(round_fights)
                current_round -= 1

            # Утешительные схватки за 3 место
            # if self.tournament.has_consolation and len(athletes) >= 4:
            #     self._generate_consolation_fights(fights, fight_number)
        except Exception as e:
            print(print("❌ Exception: ", e))

    def _generate_round_fights(self,athletes, round_number, start_fight_number, tournament_category_id):
        """Генерация схваток для одного раунда"""
        fights = []
        fight_number = start_fight_number

        for i in range(0, len(athletes), 2):
            white_athlete = athletes[i] if i < len(athletes) else None
            blue_athlete = athletes[i+1] if i+1 < len(athletes) else None

            # Пропускаем схватки где оба участника None
            if not white_athlete and not blue_athlete:
                continue

            fight = FightNew(
                tournament_category_id=tournament_category_id,
                white_athlete_id=white_athlete.id if white_athlete else None,
                blue_athlete_id=blue_athlete.id if blue_athlete else None,
                round_number=round_number,
                fight_number=fight_number,
                status=FightStatus.SCHEDULED
            )

            #сохроняем бой
            fight_repo = FightRepository()
            fight_repo.create_fight(fight)

            fights.append(fight)
            fight_number += 1

        return fights

    def _generate_consolation_fights(self, main_fights, start_fight_number):
        """Генерация утешительных схваток за 3 место"""
        if len(main_fights) < 4:
            return []

        # Находим полуфиналистов которые проиграли
        semifinal_fights = [f for f in main_fights if f.round_number == 2]
        if len(semifinal_fights) != 2:
            return []

        consolation_fights = []
        fight_number = start_fight_number

        result_repo = ResultRepository()

        # Схватка за 3 место между проигравшими в полуфиналах
        losers = []
        for fight in semifinal_fights:
            loser = result_repo.get_loser(fight.id)
            if loser:
                losers.append(loser)

        length_losers = len(losers)

        if length_losers == 2:
            fight = FightNew(
                tournament_id=self.tournament.id,
                white_athlete_id=losers[0].id,
                blue_athlete_id=losers[1].id,
                round_number=2,  # Утешительный раунд
                fight_number=fight_number,
                status=FightStatus.SCHEDULED
            )

            fight_repo = FightRepository()
            fight_repo.create_figth(fight)

        return consolation_fights

    # TODO переписать методы
    # def update_bracket(self, completed_fight):
    #     """Обновление сетки после завершения схватки"""
    #     if not completed_fight.result:
    #         return
    #
    #     winner = completed_fight.result.winner
    #     round_number = completed_fight.round_number
    #
    #     # Если это не финал, находим следующую схватку для победителя
    #     if round_number > 1:
    #         next_round = round_number - 1
    #         next_fight_number = (completed_fight.fight_number + 1) // 2
    #
    #         next_fight = Fight.query.filter_by(
    #             bracket_id=self.bracket.id,
    #             round_number=next_round,
    #             fight_number=next_fight_number
    #         ).first()
    #
    #         if next_fight:
    #             # Определяем позицию в следующей схватке
    #             if completed_fight.fight_number % 2 == 1:  # Нечетная схватка -> белый
    #                 next_fight.white_athlete_id = winner.id
    #             else:  # Четная схватка -> синий
    #                 next_fight.blue_athlete_id = winner.id
    #
    #             next_fight.save()
    #
    #     # Проверяем завершение сетки
    #     self._check_bracket_completion()
    #
    # def _check_bracket_completion(self):
    #     """Проверка завершения всей сетки"""
    #     incomplete_fights = Fight.query.filter_by(
    #         bracket_id=self.bracket.id,
    #         status='SCHEDULED'
    #     ).count()
    #
    #     if incomplete_fights == 0:
    #         self.bracket.status = 'COMPLETED'
    #         self.bracket.save()
    #
    #         # Обновляем статус турнира если все сетки завершены
    #         self._update_tournament_status()
    #
    # def _update_tournament_status(self):
    #     """Обновление статуса турнира"""
    #     incomplete_brackets = Bracket.query.filter_by(
    #         tournament_id=self.tournament.id,
    #         status='GENERATED'
    #     ).count()
    #
    #     if incomplete_brackets == 0:
    #         self.tournament.status = 'COMPLETED'
    #         self.tournament.save()

    import math

    def _generate_bracket_positions(self, participants_count: int) -> list[int]:
        """
        Генерирует позиции (1-based) для посева участников.
        Использует bit-reversal для равномерного распределения сильнейших.
        Работает для любого количества участников ≥ 1.
        """
        if participants_count <= 1:
            return [1]

        # Находим ближайшую степень двойки сверху
        n = 2 ** math.ceil(math.log2(participants_count))
        logn = int(math.log2(n))  # количество бит

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

        # Сортируем по полученным позициям (чтобы вернуть порядок: позиция 1, 2, 3, ...)
        sorted_indices = sorted(range(len(positions)), key=lambda k: positions[k])
        ordered_positions = [positions[i] for i in sorted_indices]

        return ordered_positions
    def _calculate_rounds(self,participants_count):
        """
        Расчет количества раундов для сетки
        """
        if participants_count <= 0:
            return 0

        return math.ceil(math.log2(participants_count))