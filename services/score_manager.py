from datetime import datetime
from models.result import Result
from models.fight import Fight
from databse.db import db
from config import SCORE_VALUES, OSAEKOMI_TIMES, MAX_PENALTIES


class ScoreManager:
    def __init__(self, fight_id):
        self.fight = Fight.query.get(fight_id)
        if not self.fight:
            raise ValueError(f"Fight {fight_id} not found")

        # Создаем или получаем результат
        if not self.fight.result:
            self.result = Result(fight_id=fight_id)
            db.session.add(self.result)
            db.session.commit()
        else:
            self.result = self.fight.result

    def add_yuko(self, athlete_color):
        """Добавить оценку ЮКО"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        self.result.add_score(athlete_color, 'YUKO')
        db.session.commit()

        return {
            'success': True,
            'message': f'ЮКО добавлено для {athlete_color}',
            'white_score': self.result.white_score,
            'blue_score': self.result.blue_score,
            'white_yuko': self.result.white_yuko,
            'blue_yuko': self.result.blue_yuko
        }

    def add_wazaari(self, athlete_color, technique=None):
        """Добавить оценку ВАЗА-АРИ"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        self.result.add_score(athlete_color, 'WAZAARI', technique)
        db.session.commit()

        # Проверяем, не привело ли это к победе (2 ваза-ари = иппон)
        if self.result.victory_type == 'WAZAARI_AWASETE_IPPON':
            self._complete_fight_for_winner()

        return {
            'success': True,
            'message': f'ВАЗА-АРИ добавлено для {athlete_color}',
            'white_score': self.result.white_score,
            'blue_score': self.result.blue_score,
            'white_wazaari': self.result.white_wazaari,
            'blue_wazaari': self.result.blue_wazaari,
            'victory': self.result.victory_type if self.result.victory_type else None
        }

    def add_ippon(self, athlete_color, technique=None):
        """Добавить оценку ИППОН"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        self.result.add_score(athlete_color, 'IPPON', technique)
        db.session.commit()

        # Автоматически завершаем бой при ИППОН
        self._complete_fight_for_winner()

        return {
            'success': True,
            'message': f'ИППОН добавлено для {athlete_color}. Схватка завершена!',
            'winner': self.result.winner_id,
            'victory_type': self.result.victory_type
        }

    def start_osaekomi(self, athlete_color):
        """Начать отсчет времени удержания"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        # Если уже есть активное осаекоми, сначала останавливаем его
        if self.result.osaekomi_start_time:
            self.result.stop_osaekomi()

        self.result.start_osaekomi(athlete_color)
        db.session.commit()

        return {
            'success': True,
            'message': f'ОСАЕКОМИ начато для {athlete_color}',
            'start_time': self.result.osaekomi_start_time.isoformat()
        }

    def stop_osaekomi(self):
        """Остановить отсчет времени удержания"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        if not self.result.osaekomi_start_time:
            return {'success': False, 'message': 'Нет активного ОСАЕКОМИ'}

        duration, action = self.result.stop_osaekomi()
        db.session.commit()

        result = {
            'success': True,
            'message': f'ОСАЕКОМИ остановлено после {duration} секунд',
            'duration': duration,
            'osaekomi_duration': self.result.osaekomi_duration
        }

        # Проверяем, не привело ли удержание к победе
        if duration >= OSAEKOMI_TIMES['IPPON']:
            result['ippon_awarded'] = True
            result['winner'] = self.result.winner_id
            # Завершаем бой
            self._complete_fight_for_winner()
        elif duration >= OSAEKOMI_TIMES['WAZAARI']:
            result['wazaari_awarded'] = True

            # Проверяем, не стало ли это вторым ваза-ари
            if self.result.victory_type == 'WAZAARI_AWASETE_IPPON':
                self._complete_fight_for_winner()

        return result

    def add_penalty(self, athlete_color, penalty_type):
        """Добавить штраф"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        self.result.add_penalty(athlete_color, penalty_type)
        db.session.commit()

        # Проверяем, не привело ли это к победе по штрафам
        if penalty_type.upper() == 'HANSOKU_MAKE':
            # Дисквалификация - немедленная победа противнику
            opponent_color = 'BLUE' if athlete_color.upper() == 'WHITE' else 'WHITE'
            opponent_id = self.fight.white_athlete_id if opponent_color == 'WHITE' else self.fight.blue_athlete_id

            self.result.victory_type = 'HANSOKU_MAKE'
            self.result.winner_id = opponent_id
            db.session.commit()

            self._complete_fight_for_winner()

            return {
                'success': True,
                'message': f'{penalty_type} добавлен для {athlete_color}. Дисквалификация!',
                'winner': opponent_id,
                'victory_type': 'HANSOKU_MAKE'
            }

        # Проверяем, не достиг ли спортсмен 3 шидо
        if penalty_type.upper() == 'SHIDO':
            white_count = self.result.get_penalty_count('WHITE')
            blue_count = self.result.get_penalty_count('BLUE')

            if white_count >= MAX_PENALTIES['SHIDO'] or blue_count >= MAX_PENALTIES['SHIDO']:
                self._complete_fight_for_winner()

        return {
            'success': True,
            'message': f'{penalty_type} добавлен для {athlete_color}',
            'white_penalties': self.result.white_penalties,
            'blue_penalties': self.result.blue_penalties,
            'white_penalty_count': self.result.get_penalty_count('WHITE'),
            'blue_penalty_count': self.result.get_penalty_count('BLUE')
        }

    def undo_last_action(self):
        """Отменить последнее действие"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        success, action = self.result.undo_last_action()
        if success:
            db.session.commit()
            return {
                'success': True,
                'message': 'Последнее действие отменено',
                'action_type': action['type'] if action else None
            }
        else:
            return {'success': False, 'message': 'Нет действий для отмены'}

    def reset_scores(self):
        """Сбросить все оценки и штрафы"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        self.result.reset_scores()
        db.session.commit()

        return {
            'success': True,
            'message': 'Все оценки и штрафы сброшены',
            'white_score': self.result.white_score,
            'blue_score': self.result.blue_score
        }

    def get_current_scores(self):
        """Получить текущие оценки"""
        return {
            'success': True,
            'white': {
                'score': self.result.white_score,
                'yuko': self.result.white_yuko,
                'wazaari': self.result.white_wazaari,
                'ippon': self.result.white_ippon,
                'penalties': self.result.white_penalties,
                'penalty_count': self.result.get_penalty_count('WHITE')
            },
            'blue': {
                'score': self.result.blue_score,
                'yuko': self.result.blue_yuko,
                'wazaari': self.result.blue_wazaari,
                'ippon': self.result.blue_ippon,
                'penalties': self.result.blue_penalties,
                'penalty_count': self.result.get_penalty_count('BLUE')
            },
            'osaekomi': {
                'active': self.result.osaekomi_start_time is not None,
                'athlete_color': self.result.osaekomi_athlete_color,
                'time': self.result.osaekomi_time,
                'total_duration': self.result.osaekomi_duration
            },
            'victory_type': self.result.victory_type,
            'winner_id': self.result.winner_id,
            'fight_status': self.fight.status
        }

    def _complete_fight_for_winner(self):
        """Завершить бой для текущего победителя"""
        if self.result.winner_id:
            self.fight.complete_fight(
                winner_id=self.result.winner_id,
                victory_type=self.result.victory_type,
                details=self.result.details
            )