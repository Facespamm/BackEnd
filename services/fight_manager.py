"""
Менеджер управления схватками
"""

from datetime import datetime
from database.db import db
from models.fight import Fight
from models.result import Result
from services.bracket_generator import BracketGenerator

class FightManager:
    """Менеджер управления схватками"""

    def __init__(self, fight_id=None):
        self.fight = None
        if fight_id:
            self.fight = Fight.query.get(fight_id)

    def start_fight(self, fight_id=None):
        """Начать схватку"""
        if fight_id:
            self.fight = Fight.query.get(fight_id)

        if not self.fight or self.fight.status != 'SCHEDULED':
            return False

        self.fight.status = 'LIVE'
        self.fight.start_time = datetime.utcnow()
        self.fight.timer_seconds = self.fight.tournament.fight_duration
        self.fight.timer_paused = False
        self.fight.is_golden_score = False

        return self.fight.save()

    def pause_fight(self):
        """Приостановить схватку"""
        if not self.fight or self.fight.status != 'LIVE':
            return False

        self.fight.timer_paused = True
        return self.fight.save()

    def resume_fight(self):
        """Возобновить схватку"""
        if not self.fight or self.fight.status != 'LIVE':
            return False

        self.fight.timer_paused = False
        return self.fight.save()

    def update_timer(self, seconds):
        """Обновить таймер"""
        if not self.fight or self.fight.status != 'LIVE':
            return False

        self.fight.timer_seconds = seconds
        return self.fight.save()

    def add_score(self, athlete_color, score_type):
        """Добавить оценку участнику"""
        if not self.fight or self.fight.status != 'LIVE':
            return False

        # Создаем или получаем результат
        result = self.fight.result
        if not result:
            result = Result(fight_id=self.fight.id)
            db.session.add(result)

        if score_type.upper() == 'IPPON':
            result.is_ippon = True
            result.victory_type = 'IPPON'
            # Автоматическое завершение при иппоне
            winner_id = (self.fight.white_athlete_id if athlete_color.upper() == 'WHITE' 
                        else self.fight.blue_athlete_id)
            return self.complete_fight(winner_id, 'IPPON')

        elif score_type.upper() == 'WAZAARI':
            result.is_wazaari = True
            if athlete_color.upper() == 'WHITE':
                result.white_score += 1
            else:
                result.blue_score += 1

            # Проверка двух ваза-ари
            if result.white_score >= 2:
                result.victory_type = 'WAZAARI_AWASETE_IPPON'
                return self.complete_fight(self.fight.white_athlete_id, 'WAZAARI_AWASETE_IPPON')
            elif result.blue_score >= 2:
                result.victory_type = 'WAZAARI_AWASETE_IPPON'
                return self.complete_fight(self.fight.blue_athlete_id, 'WAZAARI_AWASETE_IPPON')

        elif score_type.upper() == 'SHIDO':
            result.add_penalty(athlete_color, 'SHIDO')

            # Проверка дисквалификации по штрафам
            white_penalties = result.get_penalty_count('WHITE')
            blue_penalties = result.get_penalty_count('BLUE')

            if white_penalties >= 3:
                return self.complete_fight(self.fight.blue_athlete_id, 'SHIDO')
            elif blue_penalties >= 3:
                return self.complete_fight(self.fight.white_athlete_id, 'SHIDO')

        return result.save()

    def complete_fight(self, winner_id, victory_type, details=None):
        """Завершить схватку"""
        if not self.fight or self.fight.status != 'LIVE':
            return False

        # Создаем результат если его нет
        result = self.fight.result
        if not result:
            result = Result(fight_id=self.fight.id)
            db.session.add(result)

        # Устанавливаем результат
        result.winner_id = winner_id
        result.victory_type = victory_type
        result.details = details
        result.fight_duration = (datetime.utcnow() - self.fight.start_time).total_seconds()

        if self.fight.is_golden_score:
            result.golden_score_time = self.fight.tournament.golden_score_duration - self.fight.timer_seconds

        # Завершаем схватку
        self.fight.status = 'COMPLETED'
        self.fight.end_time = datetime.utcnow()
        self.fight.timer_paused = True

        # Сохраняем изменения
        db.session.commit()

        # Обновляем турнирную сетку
        if self.fight.bracket:
            bracket_generator = BracketGenerator(self.fight.bracket)
            bracket_generator.update_bracket(self.fight)

        return True

    def cancel_fight(self, reason):
        """Отменить схватку"""
        if not self.fight or self.fight.status not in ['SCHEDULED', 'LIVE']:
            return False

        self.fight.status = 'CANCELLED'
        self.fight.end_time = datetime.utcnow()

        # Создаем запись об отмене
        result = Result(
            fight_id=self.fight.id,
            victory_type='CANCELLED',
            details=reason
        )
        db.session.add(result)

        return db.session.commit()

    def get_fight_status(self):
        """Получить статус схватки"""
        if not self.fight:
            return None

        status_info = {
            'id': self.fight.id,
            'status': self.fight.status,
            'timer_seconds': self.fight.timer_seconds,
            'timer_paused': self.fight.timer_paused,
            'is_golden_score': self.fight.is_golden_score,
            'white_athlete': None,
            'blue_athlete': None,
            'scores': {
                'white': 0,
                'blue': 0
            },
            'penalties': {
                'white': 0,
                'blue': 0
            }
        }

        if self.fight.white_athlete:
            status_info['white_athlete'] = {
                'id': self.fight.white_athlete.id,
                'name': self.fight.white_athlete.full_name,
                'club': self.fight.white_athlete.club.name if self.fight.white_athlete.club else ''
            }

        if self.fight.blue_athlete:
            status_info['blue_athlete'] = {
                'id': self.fight.blue_athlete.id,
                'name': self.fight.blue_athlete.full_name,
                'club': self.fight.blue_athlete.club.name if self.fight.blue_athlete.club else ''
            }

        # Добавляем результаты если есть
        if self.fight.result:
            status_info['scores']['white'] = self.fight.result.white_score
            status_info['scores']['blue'] = self.fight.result.blue_score
            status_info['penalties']['white'] = self.fight.result.get_penalty_count('WHITE')
            status_info['penalties']['blue'] = self.fight.result.get_penalty_count('BLUE')

        return status_info

    @classmethod
    def get_live_fights(cls, tournament_id=None, tatami=None):
        """Получить активные схватки"""
        query = Fight.query.filter_by(status='LIVE')

        if tournament_id:
            query = query.filter_by(tournament_id=tournament_id)

        if tatami:
            query = query.filter_by(tatami=tatami)

        return query.all()

    @classmethod
    def get_scheduled_fights(cls, tournament_id=None, tatami=None):
        """Получить запланированные схватки"""
        query = Fight.query.filter_by(status='SCHEDULED')

        if tournament_id:
            query = query.filter_by(tournament_id=tournament_id)

        if tatami:
            query = query.filter_by(tatami=tatami)

        return query.order_by(Fight.scheduled_time).all()