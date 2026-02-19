from new_model.Enums import FightStatus, BracketType
from new_model.head_model.fight_new import FightNew
from repository.figth_repo import FightRepository
from repository.result_repo import ResultRepository

fight_repo = FightRepository()
result_repo = ResultRepository()

class FightGenerator:
    def generate_first_round_fights(self,athletes, round_number, start_fight_number, tournament_category_id, tatami_number,type_bracket=BracketType.MAIN):
        """Генерация схваток для одного раунда"""
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
            fight_repo.create_fight(fight)

            fights.append(fight)
            fight_number += 1

        return fights

    def generate_next_rounds_fights(self,next_fight,round_number, next_fight_number, tournament_category_id, tatami_number,type_bracket=BracketType.MAIN):
        """Генерация схваток для следующих раунда"""
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
            fight_repo.create_fight(fight)

            fights.append(fight)
            fight_number += 1

        return  fights

    def generate_consolation_fights_semifinalist(self, tournament_category_id, tatami_number,max_rounds):
        """Генерация утешительных схваток за 3 место"""
        # Находим полуфиналистов которые проиграли
        semifinal_round = max_rounds-1
        eight_round = semifinal_round -1
        return self._generate_consalation_fight(tournament_category_id, semifinal_round, eight_round, tatami_number)

    def generate_consolation_fights_finalist(self, tournament_category_id, tatami_number,max_rounds):
        """Генерация утешительных схваток за 3 место"""

        # Находим полуфиналистов которые проиграли
        final_round = max_rounds
        eight_fight = max_rounds - 2
        return self._generate_consalation_fight(tournament_category_id, final_round, eight_fight, max_rounds)

    # def _generate_group(self, fights:list[FightNew], semi_or_final_fights:FightNew)-> list[FightNew]:
    #     group = []
    #     result = result_repo.get_result_by_fight(semi_or_final_fights.id)
    #     loser = result_repo.get_loser(semi_or_final_fights.id)
    #
    #     for fight in fights:
    #         if or_(fight.white_athlete_id == result.winner_id, fight.blue_athlete_id == result.winner_id):
    #             group.append(fight)
    #         elif or_(fight.white_athlete_id == loser.id, fight.blue_athlete_id==loser.id):
    #             group.append(fight)
    #
    #     group.sort(key=lambda x: x.id,)
    #
    #     return group

    def _generate_group(self, all_fights: list[FightNew], semifinal_fight: FightNew) -> list[FightNew]:
        """
        Формирует группу бойцов для утешительной ветки.
        Включает всех, кто проиграл обоим полуфиналистам (победителю И проигравшему).
        """

        result = result_repo.get_result_by_fight(semifinal_fight.id)
        winner_id = result.winner_id
        loser_id = result_repo.get_loser(semifinal_fight.id).id

        # Оба полуфиналиста формируют эту ветку
        semifinalists = [winner_id, loser_id]

        group = []

        for fight in all_fights:
            # Проверяем, участвовал ли хотя бы один из полуфиналистов в этом бою
            fight_participants = [fight.white_athlete_id, fight.blue_athlete_id]

            for semifinalist_id in semifinalists:
                if semifinalist_id in fight_participants:
                    fight_result = result_repo.get_result_by_fight(fight.id)

                    # Если полуфиналист выиграл этот бой, добавляем его в группу
                    if fight_result and fight_result.winner_id == semifinalist_id:
                        # Избегаем дубликатов
                        if fight not in group:
                            group.append(fight)

        for fight in group:
            all_fights.remove(fight)

        # Сортируем по раундам (от раннего к позднему)
        group.sort(key=lambda x: x.round_number)
        return group

    def _generate_fights_by_group(self, group_of_fights: list[FightNew],
                                  tournament_category_id: int,
                                  tatami_number:int,
                                  branch_name: BracketType) -> list[FightNew]:
        """Создает утешительные бои для одной ветки"""

        if len(group_of_fights) < 2:
            raise Exception(f'❌ Недостаточно боев в ветке {branch_name.name}')

        # Находим проигравшего полуфиналиста
        semifinal_fight = group_of_fights[-1]  # Последний бой - это полуфинал
        semifinal_loser_id = result_repo.get_loser(semifinal_fight.id).id

        # Собираем всех остальных проигравших (кроме полуфинала)
        losers = []
        for fight in group_of_fights[:-1]:  # Исключаем сам полуфинал
            loser = result_repo.get_loser(fight.id)
            if loser and loser.id != semifinal_loser_id:  # Исключаем полуфиналиста
                losers.append({
                    'athlete_id': loser.id,
                    'round_lost': fight.round_number
                })

        if len(losers) == 0:
            raise Exception(f'❌ Нет участников для утешительной сетки в ветке {branch_name.name}')

        # Сортируем по раунду поражения (позже проигравшие начинают выше)
        losers.sort(key=lambda x: x['round_lost'], reverse=True)

        # Генерируем утешительные бои между проигравшими
        consolation_fights = []
        current_fighters = [l['athlete_id'] for l in losers]
        round_number = 1

        # Бои между обычными проигравшими
        while len(current_fighters) > 1:
            next_round_fighters = []

            for i in range(0, len(current_fighters), 2):
                if i + 1 < len(current_fighters):
                    new_fight = FightNew(
                        tournament_category_id=tournament_category_id,
                        white_athlete_id=current_fighters[i],
                        blue_athlete_id=current_fighters[i + 1],
                        round_number=round_number,
                        status=FightStatus.SCHEDULED,
                        type_bracket=branch_name,
                        tatami_number = tatami_number
                    )
                    consolation_fights.append(new_fight)
                    next_round_fighters.append(None)  # Placeholder для победителя
                else:
                    next_round_fighters.append(current_fighters[i])

            current_fighters = [f for f in next_round_fighters if f is not None]
            round_number += 1

        # Финальный бой за бронзу: победитель утешительной сетки vs проигравший полуфиналист
        if len(current_fighters) == 1:
            bronze_fight = FightNew(
                tournament_category_id=tournament_category_id,
                white_athlete_id=current_fighters[0],  # Победитель утешительных боев
                blue_athlete_id=semifinal_loser_id,  # Проигравший полуфиналист
                round_number=round_number,
                status=FightStatus.SCHEDULED,
                type_bracket=branch_name,  # Финал за бронзу
                tatami_number = tatami_number
            )
            consolation_fights.append(bronze_fight)

        return consolation_fights

    def _generate_consalation_fight(self, tournament_category_id, round, eight_round,tatami_number) -> list[FightNew]:
        all_fights = fight_repo.get_semi_final_fights(tournament_category_id, round, eight_round)

        if len(all_fights) < 2:
            raise Exception("❌ Недостаточно полуфиналистов для утешительных боев")

        semifinal_fights = [fight for fight in all_fights if fight.round_number == round]
        if len(semifinal_fights) != 2 or not len(semifinal_fights):
            raise Exception('❌ Нет боев полуфиналистов')

        group_a = self._generate_group(all_fights, semifinal_fights[0])
        group_b = self._generate_group(all_fights, semifinal_fights[1])

        consolation_fights_a = self._generate_fights_by_group(group_a, tournament_category_id, tatami_number,
                                                              BracketType.CONSOLATION_GROUP_A)
        consolation_fights_b = self._generate_fights_by_group(group_b, tournament_category_id, tatami_number,
                                                              BracketType.CONSOLATION_GROUP_B)

        return consolation_fights_a + consolation_fights_b