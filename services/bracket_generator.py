"""
Генератор турнирных сеток по правилам дзюдо
"""

import math
import random
from database.db import db
from models.fight import Fight
from models.bracket import Bracket
from utils.helpers import calculate_rounds, generate_bracket_positions

class BracketGenerator:
    """Генератор турнирных сеток"""

    def __init__(self, bracket):
        self.bracket = bracket
        self.tournament = bracket.tournament
        self.category = bracket.category
        self.athletes = bracket.category.athletes

    def generate(self):
        """Генерация сетки по олимпийской системе"""
        if not self.athletes:
            return []

        athletes_count = len(self.athletes)
        if athletes_count < 2:
            return []

        # Очищаем существующие схватки
        Fight.query.filter_by(bracket_id=self.bracket.id).delete()

        # Определяем количество раундов
        total_rounds = calculate_rounds(athletes_count)
        self.bracket.max_rounds = total_rounds

        # Seed участников (сильнейшие не встречаются в первых раундах)
        seeded_athletes = self._seed_athletes()

        # Генерируем схватки
        fights = self._generate_fights(seeded_athletes, total_rounds)

        # Сохраняем сетку
        self.bracket.status = 'GENERATED'
        self.bracket.save()

        return fights

    def _seed_athletes(self):
        """Посев участников (сильнейшие распределяются)"""
        athletes = list(self.athletes)

        # Сортируем по рейтингу (если есть) или случайно
        try:
            # Попытка сортировки по рейтингу (можно добавить логику рейтинга)
            athletes.sort(key=lambda a: a.get_victories_count() if hasattr(a, 'get_victories_count') else 0, reverse=True)
        except:
            # Случайное перемешивание если нет данных
            random.shuffle(athletes)

        # Применяем seeding позиции
        positions = generate_bracket_positions(len(athletes))
        seeded_athletes = [None] * len(positions)

        for i, pos in enumerate(positions):
            if i < len(athletes):
                seeded_athletes[pos-1] = athletes[i]

        # Убираем None значения (если участников меньше чем позиций)
        return [a for a in seeded_athletes if a is not None]

    def _generate_fights(self, athletes, total_rounds):
        """Генерация схваток для всех раундов"""
        fights = []
        current_round = total_rounds
        current_athletes = athletes.copy()
        fight_number = 1

        # Генерация первого раунда
        round_fights = self._generate_round_fights(current_athletes, current_round, fight_number)
        fights.extend(round_fights)

        # winners для следующего раунда
        next_athletes = []
        for fight in round_fights:
            # Создаем "пустых" победителей для следующего раунда
            next_athletes.append(None)

        fight_number += len(round_fights)
        current_round -= 1

        # Генерация последующих раундов
        while current_round > 0:
            round_fights = self._generate_round_fights(next_athletes, current_round, fight_number)
            fights.extend(round_fights)

            # Обновляем next_athletes для следующего раунда
            next_athletes = [None] * (len(round_fights) // 2)
            fight_number += len(round_fights)
            current_round -= 1

        # Утешительные схватки за 3 место
        if self.bracket.has_consolation and len(athletes) >= 4:
            consolation_fights = self._generate_consolation_fights(fights, fight_number)
            fights.extend(consolation_fights)

        # Сохраняем все схватки
        for fight in fights:
            fight.save()

        return fights

    def _generate_round_fights(self, athletes, round_number, start_fight_number):
        """Генерация схваток для одного раунда"""
        fights = []
        fight_number = start_fight_number

        for i in range(0, len(athletes), 2):
            white_athlete = athletes[i] if i < len(athletes) else None
            blue_athlete = athletes[i+1] if i+1 < len(athletes) else None

            # Пропускаем схватки где оба участника None
            if not white_athlete and not blue_athlete:
                continue

            fight = Fight(
                tournament_id=self.tournament.id,
                bracket_id=self.bracket.id,
                category_id=self.category.id,
                white_athlete_id=white_athlete.id if white_athlete else None,
                blue_athlete_id=blue_athlete.id if blue_athlete else None,
                round_number=round_number,
                fight_number=fight_number,
                status='SCHEDULED'
            )

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

        # Схватка за 3 место между проигравшими в полуфиналах
        losers = []
        for fight in semifinal_fights:
            if fight.result:
                loser = fight.get_loser()
                if loser:
                    losers.append(loser)

        if len(losers) == 2:
            fight = Fight(
                tournament_id=self.tournament.id,
                bracket_id=self.bracket.id,
                category_id=self.category.id,
                white_athlete_id=losers[0].id,
                blue_athlete_id=losers[1].id,
                round_number=2,  # Утешительный раунд
                fight_number=fight_number,
                status='SCHEDULED'
            )
            consolation_fights.append(fight)

        return consolation_fights

    def update_bracket(self, completed_fight):
        """Обновление сетки после завершения схватки"""
        if not completed_fight.result:
            return

        winner = completed_fight.result.winner
        round_number = completed_fight.round_number

        # Если это не финал, находим следующую схватку для победителя
        if round_number > 1:
            next_round = round_number - 1
            next_fight_number = (completed_fight.fight_number + 1) // 2

            next_fight = Fight.query.filter_by(
                bracket_id=self.bracket.id,
                round_number=next_round,
                fight_number=next_fight_number
            ).first()

            if next_fight:
                # Определяем позицию в следующей схватке
                if completed_fight.fight_number % 2 == 1:  # Нечетная схватка -> белый
                    next_fight.white_athlete_id = winner.id
                else:  # Четная схватка -> синий
                    next_fight.blue_athlete_id = winner.id

                next_fight.save()

        # Проверяем завершение сетки
        self._check_bracket_completion()

    def _check_bracket_completion(self):
        """Проверка завершения всей сетки"""
        incomplete_fights = Fight.query.filter_by(
            bracket_id=self.bracket.id,
            status='SCHEDULED'
        ).count()

        if incomplete_fights == 0:
            self.bracket.status = 'COMPLETED'
            self.bracket.save()

            # Обновляем статус турнира если все сетки завершены
            self._update_tournament_status()

    def _update_tournament_status(self):
        """Обновление статуса турнира"""
        incomplete_brackets = Bracket.query.filter_by(
            tournament_id=self.tournament.id,
            status='GENERATED'
        ).count()

        if incomplete_brackets == 0:
            self.tournament.status = 'COMPLETED'
            self.tournament.save()