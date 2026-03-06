from new_model.Enums import FightStatus, BracketType
from new_model.head_model.fight_new import FightNew
from repository.athlete_repo import AthleteRepository
from repository.figth_repo import FightRepository
from repository.result_repo import ResultRepository
from utils.helpers import calculate_rounds

class FightGenerator:

    def __init__(self, session):
        self.fight_repo = FightRepository(session)
        self.result_repo = ResultRepository(session)
        self.athlete_repo = AthleteRepository(session)

    def generate_first_round_fights(self,athletes, round_number, start_fight_number, tournament_category_id, tatami_number,type_bracket=BracketType.MAIN):
        """    Генерирует схватки для первого раунда турнира.

            Разбивает список спортсменов на пары (белый/синий).
            Если спортсменов нечётное количество — последний получает пустого соперника (None).
            Схватки, где оба участника None, пропускаются.

            Args:
                athletes: Список спортсменов для жеребьёвки.
                round_number: Номер раунда.
                start_fight_number: Стартовый номер схватки.
                tournament_category_id: ID категории турнира.
                tatami_number: Номер татами.
                type_bracket: Тип сетки (основная, утешительная и т.д.).

            Returns:
                Список созданных и сохранённых схваток.
          """

        fights = []
        fight_number = start_fight_number

        athlete_count = len(athletes)
        for i in range(0, len(athletes), 2):
            white_athlete = athletes[i] if i < athlete_count else None
            blue_athlete = athletes[i+1] if i+1 < athlete_count else None

            # Пропускаем схватки где оба участника None
            if not white_athlete and not blue_athlete:
                continue

            fight = FightNew(
                tournament_category_id=tournament_category_id,
                white_athlete_id=white_athlete.id if white_athlete else None,
                blue_athlete_id=blue_athlete.id if blue_athlete else None,
                round_number=round_number,
                fight_number=fight_number,
                status=FightStatus.SCHEDULED,
                type_bracket = type_bracket,
                tatami_number = tatami_number
            )

            #сохроняем бой
            self.fight_repo.create_fight(fight)

            fights.append(fight)
            fight_number += 1

        return fights

    def generate_next_rounds_fights(self,next_fight,round_number, next_fight_number, tournament_category_id, tatami_number,type_bracket=BracketType.MAIN):
        """Генерирует пустые схватки для последующих раундов турнира.

            Создаёт схватки без участников (white/blue = None) —
            победители заполняются по мере завершения предыдущего раунда.

            Args:
                next_fight: Список схваток предыдущего раунда,
                            определяет количество новых схваток.
                round_number: Номер раунда.
                next_fight_number: Стартовый номер схватки.
                tournament_category_id: ID категории турнира.
                tatami_number: Номер татами.
                type_bracket: Тип сетки (основная, утешительная и т.д.).

            Returns:
                Список созданных и сохранённых схваток.
        """
        fights = []
        fight_number = next_fight_number

        length_next_fight = len(next_fight)
        for i in range(length_next_fight):
            fight = FightNew(
                tournament_category_id=tournament_category_id,
                white_athlete_id=None,
                blue_athlete_id=None,
                round_number=round_number,
                fight_number=fight_number,
                status=FightStatus.SCHEDULED,
                type_bracket=type_bracket,
                tatami_number = tatami_number
            )

            # сохроняем бой
            self.fight_repo.create_fight(fight)

            fights.append(fight)
            fight_number += 1

        return  fights

    def generate_consolation_fights_semifinalist(self, tournament_category_id, tatami_number, max_rounds):
        semifinal_round = max_rounds - 1
        eight_round = semifinal_round - 1
        print(f"max_rounds={max_rounds}, semifinal_round={semifinal_round}, eight_round={eight_round}")

        all_fights = self.fight_repo.get_untracked_semifinal_fights(tournament_category_id, semifinal_round,
                                                                    eight_round)
        print(f"all_fights: {[(f.id, f.round_number) for f in all_fights]}")

        semifinal_fights = [f for f in all_fights if f.round_number == semifinal_round]
        print(f"semifinal_fights: {[(f.id, f.round_number) for f in semifinal_fights]}")

        return self._generate_semifinalist_fight(tournament_category_id, semifinal_round, eight_round, tatami_number)

    def generate_consolation_fights_finalist(self, tournament_category_id, tatami_number, max_rounds):
        final_round = max_rounds
        eight_fight = max(1, max_rounds - 2)  # минимум 1
        return self._generate_finalist_fight(tournament_category_id, final_round, eight_fight, tatami_number)
    def _generate_group(self, all_fights: list[FightNew], semifinal_fight: FightNew) -> list[FightNew]:
        """
        Формирует группу бойцов для утешительной ветки.
        Включает всех, кто проиграл обоим полуфиналистам (победителю И проигравшему).
        """

        result = self.result_repo.get_result_by_fight(semifinal_fight.id)
        winner_id = result.winner_id
        loser_id = self.result_repo.get_loser(semifinal_fight.id).id

        # Оба полуфиналиста формируют эту ветку
        semifinalists = [winner_id, loser_id]

        group = []

        for fight in all_fights:
            # Проверяем, участвовал ли хотя бы один из полуфиналистов в этом бою
            fight_participants = [fight.white_athlete_id, fight.blue_athlete_id]

            for semifinalist_id in semifinalists:
                if semifinalist_id in fight_participants:
                    fight_result = self.result_repo.get_result_by_fight(fight.id)

                    # Если полуфиналист выиграл этот бой, добавляем его в группу
                    if fight_result and fight_result.winner_id == semifinalist_id:
                        # Избегаем дубликатов
                        if fight not in group:
                            group.append(fight)

        # Сортируем по раундам (от раннего к позднему)
        group.sort(key=lambda x: x.round_number)
        return group

    def _generate_fights_semifinalist_by_group(self, group_of_fights: list[FightNew],
                                  tournament_category_id: int,
                                  tatami_number:int,
                                  branch_name: BracketType) -> list[FightNew]:
        """Создает утешительные бои для одной ветки"""
        if len(group_of_fights) < 2:
            raise Exception(f'❌ Недостаточно боев в ветке {branch_name.name}')

        # Находим проигравшего полуфиналиста
        semifinal_fight = group_of_fights[-1]  # Последний бой - это полуфинал
        semifinal_loser_id = self.result_repo.get_loser(semifinal_fight.id).id

        # Собираем всех остальных проигравших (кроме полуфинала)
        losers = [
            {'athlete_id': loser, 'round_lost': fight.round_number}
            for fight in group_of_fights
            if (loser := self.result_repo.get_loser(fight.id)) and loser.id != semifinal_loser_id
        ]

        if len(losers) == 0:
            raise Exception(f'❌ Нет участников для утешительной сетки в ветке {branch_name.name}')

        # Сортируем по раунду поражения (позже проигравшие начинают выше)
        losers.sort(key=lambda x: x['round_lost'], reverse=True)
        athlete_count = len(losers)
        total_round = calculate_rounds(athlete_count)

        # Генерируем утешительные бои между проигравшими
        consolation_fights = []
        current_fighters = [l['athlete_id'] for l in losers]
        current_round = 1
        fight_number = 1

        first_fights = self.generate_first_round_fights(current_fighters,current_round,fight_number,tournament_category_id,tatami_number, branch_name)
        if not first_fights:
            raise Exception('Error create consalation fights')

        consolation_fights.extend(first_fights)
        fight_number += len(consolation_fights)
        current_round += 1

        if len(consolation_fights) == 1:
            first_fight = consolation_fights[0]

            color_loser_semifinalist = 'white' if semifinal_loser_id == semifinal_fight.white_athlete_id else 'blue'

            next_figth = FightNew(
                tournament_category_id=tournament_category_id,
                white_athlete_id= semifinal_loser_id if color_loser_semifinalist == 'blue' else None,
                blue_athlete_id=semifinal_loser_id if color_loser_semifinalist == 'white' else None,
                round_number=current_round,
                fight_number=fight_number,
                status=FightStatus.SCHEDULED,
                type_bracket=branch_name,
                tatami_number=tatami_number
            )

            is_added = self.fight_repo.create_fight(next_figth)
            self.fight_repo.update_fight(first_fight.id, next_figth.id)
            consolation_fights.append(next_figth)

        return consolation_fights

    def _generate_semifinalist_fight(self, tournament_category_id, round, eight_round,tatami_number) -> list[FightNew]:
        all_fights = self.fight_repo.get_untracked_semifinal_fights(tournament_category_id, round, eight_round)

        if len(all_fights) < 2:
            raise Exception("❌ Недостаточно полуфиналистов для утешительных боев")

        semifinal_fights = [fight for fight in all_fights if fight.round_number == round]
        if len(semifinal_fights) != 2 or not len(semifinal_fights):
            raise Exception('❌ Нет боев полуфиналистов')

        group_a = self._generate_group(all_fights, semifinal_fights[0])
        group_b = self._generate_group(all_fights, semifinal_fights[1])

        consolation_fights_a = self._generate_fights_semifinalist_by_group(group_a, tournament_category_id, tatami_number,
                                                              BracketType.SEMIFINALIST_CONSOLATION_GROUP_A)
        consolation_fights_b = self._generate_fights_semifinalist_by_group(group_b, tournament_category_id, tatami_number,
                                                              BracketType.SEMIFINALIST_CONSOLATION_GROUP_B)

        return consolation_fights_a + consolation_fights_b

    def _generate_fights_finalist_by_group(self, group_of_fights: list[FightNew],
                                  tournament_category_id: int,
                                  tatami_number:int,
                                  branch_name: BracketType) -> FightNew:
        """Создает утешительные бои для одной ветки"""
        if len(group_of_fights) < 1:
            raise Exception(f'❌ Недостаточно боев в ветке {branch_name.name}')

        # Собираем всех остальных проигравших (кроме полуфинала)
        losers = [
            {'athlete_id': loser, 'round_lost': fight.round_number}
            for fight in group_of_fights
            if (loser := self.result_repo.get_loser(fight.id))
        ]

        if len(losers) == 0:
            raise Exception(f'❌ Нет участников для утешительной сетки в ветке {branch_name.name}')

        losers.sort(key=lambda x: x['round_lost'], reverse=True)
        athlete_count = len(losers)

        # Генерируем утешительные бои между проигравшими
        current_fighters = [l['athlete_id'] for l in losers]
        current_round = 1
        fight_number = 1

        first_fights = self.generate_first_round_fights(current_fighters, current_round, fight_number,
                                                        tournament_category_id, tatami_number, branch_name)

        if first_fights[0].white_athlete_id is None or first_fights[0].blue_athlete_id is None:
            self.fight_repo.update_status(first_fights[0].id, FightStatus.COMPLETED)

        return first_fights[0]

    def _generate_final_group(self, all_fights: list[FightNew], final_athlete_id: int, final_id: int) -> list[FightNew]:
        group = []

        for fight in all_fights:
            # Проверяем, участвовал ли хотя бы один из полуфиналистов в этом бою
            fight_result = self.result_repo.get_result_by_fight(fight.id)

            if fight_result and fight_result.winner_id == final_athlete_id and fight.id != final_id:
            # Избегаем дубликатов
                if fight not in group:
                    group.append(fight)

        # Сортируем по раундам (от раннего к позднему)
        group.sort(key=lambda x: x.round_number)
        return group

    def _generate_finalist_fight(self, tournament_category_id, round, eight_round, tatami_number) -> list[FightNew]:
        all_fights = self.fight_repo.get_untracked_semifinal_fights(tournament_category_id, round, eight_round)

        if len(all_fights) < 2:
            raise Exception("❌ Недостаточно финалистов для утешительных боев")

        # ← берём реальный максимальный раунд из боёв а не из параметра
        real_final_round = max(f.round_number for f in all_fights)

        final_fights = [fight for fight in all_fights if fight.round_number == real_final_round]
        if len(final_fights) != 1:
            raise Exception('❌ Нет боев финалистов')

        winner_id = self.result_repo.get_result_by_fight(final_fights[0].id).winner_id
        losser_id = self.result_repo.get_loser(final_fights[0].id).id

        group_a = self._generate_final_group(all_fights, winner_id, final_fights[0].id)
        group_b = self._generate_final_group(all_fights, losser_id, final_fights[0].id)

        fights_group_a = self._generate_fights_finalist_by_group(group_a, tournament_category_id, tatami_number,
                                                                 BracketType.FINALIST_CONSOLATION_GROUP_A)
        fights_group_b = self._generate_fights_finalist_by_group(group_b, tournament_category_id, tatami_number,
                                                                 BracketType.FINALIST_CONSOLATION_GROUP_B)

        return [fights_group_a, fights_group_b]