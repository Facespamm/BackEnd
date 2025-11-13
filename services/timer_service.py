"""
Сервис управления таймерами схваток
"""

import threading
import time
from datetime import datetime, timedelta
from database.db import db
from models.fight import Fight
from services.fight_manager import FightManager

class TimerService:
    """Сервис управления таймерами"""

    _instance = None
    _timers = {}
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TimerService, cls).__new__(cls)
        return cls._instance

    def start_timer(self, fight_id):
        """Запустить таймер для схватки"""
        with self._lock:
            if fight_id in self._timers:
                return False

            fight = Fight.query.get(fight_id)
            if not fight or fight.status != 'LIVE':
                return False

            # Создаем поток для таймера
            timer_thread = threading.Thread(
                target=self._timer_worker,
                args=(fight_id,),
                daemon=True
            )

            self._timers[fight_id] = {
                'thread': timer_thread,
                'running': True,
                'last_update': datetime.utcnow()
            }

            timer_thread.start()
            return True

    def stop_timer(self, fight_id):
        """Остановить таймер для схватки"""
        with self._lock:
            if fight_id in self._timers:
                self._timers[fight_id]['running'] = False
                del self._timers[fight_id]
                return True
            return False

    def pause_timer(self, fight_id):
        """Приостановить таймер"""
        fight = Fight.query.get(fight_id)
        if fight and fight.status == 'LIVE':
            fight.timer_paused = True
            return fight.save()
        return False

    def resume_timer(self, fight_id):
        """Возобновить таймер"""
        fight = Fight.query.get(fight_id)
        if fight and fight.status == 'LIVE' and fight.timer_paused:
            fight.timer_paused = False
            return fight.save()
        return False

    def set_timer(self, fight_id, seconds):
        """Установить значение таймера"""
        fight = Fight.query.get(fight_id)
        if fight and fight.status == 'LIVE':
            fight.timer_seconds = seconds
            return fight.save()
        return False

    def _timer_worker(self, fight_id):
        """Рабочий поток таймера"""
        while fight_id in self._timers and self._timers[fight_id]['running']:
            try:
                fight = Fight.query.get(fight_id)
                if not fight or fight.status != 'LIVE':
                    self.stop_timer(fight_id)
                    break

                # Обновляем время только если таймер не на паузе
                if not fight.timer_paused and fight.timer_seconds > 0:
                    fight.timer_seconds -= 1

                    # Автоматическое сохранение каждые 5 секунд
                    current_time = datetime.utcnow()
                    last_update = self._timers[fight_id]['last_update']

                    if (current_time - last_update).total_seconds() >= 5:
                        fight.save()
                        self._timers[fight_id]['last_update'] = current_time

                    # Проверка окончания времени
                    if fight.timer_seconds <= 0:
                        self._handle_time_expired(fight)

                time.sleep(1)

            except Exception as e:
                print(f"Ошибка в таймере {fight_id}: {e}")
                break

        # Очистка при выходе
        with self._lock:
            if fight_id in self._timers:
                del self._timers[fight_id]

    def _handle_time_expired(self, fight):
        """Обработка окончания времени"""
        fight_manager = FightManager(fight.id)

        if fight.is_golden_score:
            # В золотом скоре - победа по решению судей
            # Здесь можно добавить логику определения победителя по очкам
            if fight.result:
                if fight.result.white_score > fight.result.blue_score:
                    fight_manager.complete_fight(fight.white_athlete_id, 'WAZAARI')
                elif fight.result.blue_score > fight.result.white_score:
                    fight_manager.complete_fight(fight.blue_athlete_id, 'WAZAARI')
                else:
                    # Ничья - победа по решению судей (можно добавить логику)
                    fight_manager.complete_fight(fight.white_athlete_id, 'WAZAARI')
        else:
            # Переход в золотой скор
            fight.is_golden_score = True
            fight.timer_seconds = fight.tournament.golden_score_duration
            fight.save()

    def get_timer_status(self, fight_id):
        """Получить статус таймера"""
        fight = Fight.query.get(fight_id)
        if not fight:
            return None

        return {
            'fight_id': fight.id,
            'seconds': fight.timer_seconds,
            'paused': fight.timer_paused,
            'is_golden_score': fight.is_golden_score,
            'status': fight.status
        }

    def get_all_active_timers(self):
        """Получить все активные таймеры"""
        active_fights = Fight.query.filter_by(status='LIVE').all()
        timers = {}

        for fight in active_fights:
            timers[fight.id] = self.get_timer_status(fight.id)

        return timers

    def cleanup_timers(self):
        """Очистка таймеров для завершенных схваток"""
        with self._lock:
            fights_to_remove = []

            for fight_id in self._timers:
                fight = Fight.query.get(fight_id)
                if not fight or fight.status != 'LIVE':
                    fights_to_remove.append(fight_id)

            for fight_id in fights_to_remove:
                if fight_id in self._timers:
                    self._timers[fight_id]['running'] = False
                    del self._timers[fight_id]

    @classmethod
    def get_instance(cls):
        """Получить экземпляр сервиса (singleton)"""
        if cls._instance is None:
            cls._instance = TimerService()
        return cls._instance