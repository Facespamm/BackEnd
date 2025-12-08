"""
Менеджер управления схватками
"""

from datetime import datetime

from sqlalchemy.orm.sync import update

from databse.db import db
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
        try:
            if fight_id:
                self.fight = Fight.query.get(fight_id)

            if not self.fight:
                print(f"Схватка не найдена: {fight_id}")
                return False

            print(f"Текущий статус схватки: {self.fight.status}")

            # Разрешаем начинать схватку из статусов SCHEDULED или CANCELLED
            if self.fight.status not in ['SCHEDULED', 'CANCELLED']:
                print(f"Невозможно начать схватку со статусом: {self.fight.status}")
                return False

            # Используем LIVE для соответствия API
            self.fight.status = 'LIVE'
            self.fight.start_time = datetime.utcnow()

            # Устанавливаем время боя из настроек турнира
            tournament = self.fight.tournament
            if tournament and tournament.fight_duration:
                self.fight.timer_seconds = tournament.fight_duration
            else:
                self.fight.timer_seconds = 300  # значение по умолчанию 5 минут

            self.fight.is_golden_score = False

            print(f"Сохранение схватки с таймером: {self.fight.timer_seconds} секунд")

            # Прямое сохранение через db.session
            db.session.add(self.fight)
            db.session.commit()

            print("Схватка успешно начата")
            return True

        except Exception as e:
            print(f"Ошибка при начале схватки: {str(e)}")
            db.session.rollback()
            return False

    def finish_fight(self):
        """Завершить схватку (без определения победителя)"""
        try:
            if not self.fight or self.fight.status != 'LIVE':
                print(f"Невозможно завершить схватку со статусом: {self.fight.status if self.fight else 'None'}")
                return False

            query = (
                update(Fight)
                .value(status='COMPLETED',end_time=datetime.utcnow(),timer_seconds=0)
                .fiter_by(id=Fight.id)
            )
            db.session.execute(query)
            db.session.commit()


            print("Схватка успешно завершена")
            return True

        except Exception as e:
            print(f"Ошибка при завершении схватки: {str(e)}")
            db.session.rollback()
            return False

    def update_timer(self, seconds):
        """Обновить таймер"""
        try:
            if not self.fight or self.fight.status != 'LIVE':
                return False

            self.fight.timer_seconds = seconds
            db.session.add(self.fight)
            db.session.commit()
            return True

        except Exception as e:
            print(f"Ошибка при обновлении таймера: {str(e)}")
            db.session.rollback()
            return False

    def add_score(self, athlete_color, score_type):
        """Добавить оценку участнику"""
        try:
            if not self.fight or self.fight.status != 'LIVE':
                return False

            # Создаем или получаем результат
            result = self.fight.result
            if not result:
                result = Result(fight_id=self.fight.id)
                db.session.add(result)

            score_type = score_type.upper()
            athlete_color = athlete_color.upper()

            if score_type == 'IPPON':
                result.is_ippon = True
                result.victory_type = 'IPPON'
                # Автоматическое завершение при иппоне
                winner_id = (self.fight.white_athlete_id if athlete_color == 'WHITE'
                            else self.fight.blue_athlete_id)
                return self.complete_fight(winner_id, 'IPPON')

            elif score_type == 'WAZAARI':
                result.is_wazaari = True
                if athlete_color == 'WHITE':
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

            elif score_type == 'SHIDO':
                result.add_penalty(athlete_color, 'SHIDO')

                # Проверка дисквалификации по штрафам
                white_penalties = result.get_penalty_count('WHITE')
                blue_penalties = result.get_penalty_count('BLUE')

                if white_penalties >= 3:
                    return self.complete_fight(self.fight.blue_athlete_id, 'SHIDO')
                elif blue_penalties >= 3:
                    return self.complete_fight(self.fight.white_athlete_id, 'SHIDO')

            db.session.commit()
            return True

        except Exception as e:
            print(f"Ошибка при добавлении оценки: {str(e)}")
            db.session.rollback()
            return False

    def complete_fight(self, winner_id, victory_type, details=None):
        """Завершить схватку с определением победителя"""
        try:
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
            if self.fight.start_time:
                result.fight_duration = (datetime.utcnow() - self.fight.start_time).total_seconds()

            if self.fight.is_golden_score:
                result.golden_score_time = self.fight.tournament.golden_score_duration - self.fight.timer_seconds

            # Завершаем схватку
            self.fight.status = 'COMPLETED'
            self.fight.end_time = datetime.utcnow()
            self.fight.timer_seconds = 0

            # Сохраняем изменения
            db.session.commit()

            # Обновляем турнирную сетку
            if self.fight.bracket:
                bracket_generator = BracketGenerator(self.fight.bracket)
                bracket_generator.update_bracket(self.fight)

            return True

        except Exception as e:
            print(f"Ошибка при завершении схватки с победителем: {str(e)}")
            db.session.rollback()
            return False

    def cancel_fight(self, reason):
        """Отменить схватку"""
        try:
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
            db.session.add(self.fight)
            db.session.commit()

            return True

        except Exception as e:
            print(f"Ошибка при отмене схватки: {str(e)}")
            db.session.rollback()
            return False

    def get_fight_status(self):
        """Получить статус схватки"""
        if not self.fight:
            return None

        status_info = {
            'id': self.fight.id,
            'status': self.fight.status,
            'timer_seconds': self.fight.timer_seconds,
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

    # В fight_manager.py добавляем два новых метода в класс FightManager:


    def reset_fight(self):
        """Полный сброс схватки для переигровки - САМЫЙ ПРОСТОЙ ВАРИАНТ"""
        try:
            if not self.fight:
                return {'success': False, 'error': 'Схватка не найдена'}

            fight_id = self.fight.id

            # НЕ удаляем результат, а очищаем его
            if self.fight.result:
                result = self.fight.result
                # Очищаем все поля результата
                result.winner_id = None
                result.victory_type = None
                result.details = None
                result.white_score = 0
                result.blue_score = 0
                result.white_penalties = None
                result.blue_penalties = None
                result.fight_duration = None
                result.golden_score_time = None
                result.technique_used = None
                result.is_ippon = False
                result.is_wazaari = False
                # Добавляем если есть юко
                if hasattr(result, 'white_yuko'):
                    result.white_yuko = 0
                    result.blue_yuko = 0

            # Сбрасываем статус схватки
            self.fight.status = 'SCHEDULED'
            self.fight.start_time = None
            self.fight.end_time = None
            self.fight.timer_seconds = self.fight.tournament.fight_duration if self.fight.tournament else 300
            self.fight.is_golden_score = False
            self.fight.timer_paused = True

            db.session.commit()

            return {
                'success': True,
                'message': 'Схватка сброшена для переигровки',
                'fight_id': fight_id,
                'new_status': 'SCHEDULED'
            }

        except Exception as e:
            db.session.rollback()
            print(f"Ошибка в reset_fight: {str(e)}")
            return {'success': False, 'error': f"Ошибка сброса: {str(e)}"}
    @classmethod
    def get_scheduled_fights(cls, tournament_id=None, tatami=None):
        """Получить запланированные схватки"""
        query = Fight.query.filter_by(status='SCHEDULED')

        if tournament_id:
            query = query.filter_by(tournament_id=tournament_id)

        if tatami:
            query = query.filter_by(tatami=tatami)

        return query.order_by(Fight.scheduled_time).all()