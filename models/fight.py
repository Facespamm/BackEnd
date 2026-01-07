from datetime import datetime
from databse.db import db


class Fight(db.Model):
    """
    Модель схватки
    """
    __tablename__ = 'fights'

    # Основная информация
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    bracket_id = db.Column(db.Integer, db.ForeignKey('brackets.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    # Участники
    white_athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'))
    blue_athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'))

    # Информация о схватке
    tatami = db.Column(db.Integer, default=1)
    round_number = db.Column(db.Integer, default=1)  # Раунд в сетке
    fight_number = db.Column(db.Integer)  # Номер схватки
    scheduled_time = db.Column(db.DateTime)

    # Статус схватки
    status = db.Column(db.String(20), default='SCHEDULED')  # SCHEDULED, LIVE, COMPLETED, CANCELLED, REPLAY
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

    # Судьи
    main_referee = db.Column(db.String(100))
    judge1 = db.Column(db.String(100))
    judge2 = db.Column(db.String(100))

    # Журнал событий боя
    events_log = db.Column(db.JSON, default=list)  # Все события боя в одном месте

    # Связи
    tournament = db.relationship('Tournament', back_populates='fights')
    bracket = db.relationship('Bracket', back_populates='fights')
    category = db.relationship('Category', back_populates='fights')
    result = db.relationship('Result', back_populates='fight', cascade='all, delete-orphan')

    white_athlete = db.relationship('Athlete',
                                    foreign_keys=[white_athlete_id],
                                    back_populates='fights_as_white')
    blue_athlete = db.relationship('Athlete',
                                   foreign_keys=[blue_athlete_id],
                                   back_populates='fights_as_blue')

    def __repr__(self):
        return f'<Fight {self.fight_number} - Round {self.round_number}>'

    @property
    def duration(self):
        """Длительность схватки в секундах (только для завершенных)"""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds())
        return 0

    @property
    def is_ready_to_start(self):
        """Готова ли схватка к началу"""
        return (self.white_athlete_id is not None and
                self.blue_athlete_id is not None and
                self.status == 'SCHEDULED')

    @property
    def has_active_osaekomi(self):
        """Есть ли активное осаекоми"""
        return self.result and self.result.osaekomi_start_time is not None

    @property
    def osaekomi_time(self):
        """Время текущего осаекоми"""
        if self.has_active_osaekomi:
            return self.result.osaekomi_time
        return 0

    def next_fight(self):
        """Следующая схватка в сетке"""
        if self.bracket_id:
            return Fight.query.filter(
                Fight.bracket_id == self.bracket_id,
                Fight.round_number == self.round_number,
                Fight.fight_number == self.fight_number + 1
            ).first()
        return None

    def start_fight(self):
        """Начать схватку"""
        if self.status == 'SCHEDULED':
            self.status = 'LIVE'
            self.start_time = datetime.utcnow()

            # Инициализируем таймер с начальным значением
            self.timer_seconds = self.fight_minutes * 60
            self.is_golden_score = False

            # Добавляем событие начала боя
            self._add_initial_event()

            self.save()
            return True
        return False

    def _add_initial_event(self):
        """Добавить начальное событие боя"""
        if not self.events_log:
            self.events_log = []

        initial_event = {
            'id': 1,
            'type': 'SYSTEM',
            'subtype': 'FIGHT_START',
            'description': 'Бой начат',
            'match_time': '0:00',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'fight_minutes': self.fight_minutes,
                'white_athlete_id': self.white_athlete_id,
                'blue_athlete_id': self.blue_athlete_id
            }
        }
        self.events_log.append(initial_event)

    def enter_golden_score(self):
        """Перейти в золотой скор"""
        if self.status == 'LIVE' and self.timer_seconds <= 0:
            self.is_golden_score = True
            self.timer_seconds = self.golden_score_minutes * 60

            # Добавляем событие перехода в золотой скор
            golden_score_event = {
                'id': len(self.events_log) + 1,
                'type': 'SYSTEM',
                'subtype': 'GOLDEN_SCORE_START',
                'description': 'Переход в золотой скор',
                'match_time': self._get_current_match_time(),
                'timestamp': datetime.utcnow().isoformat(),
                'details': {
                    'golden_score_minutes': self.golden_score_minutes
                }
            }
            self.events_log.append(golden_score_event)

            self.save()
            return True
        return False

    def _get_current_match_time(self):
        """Получить текущее время боя (минута:секунда)"""
        if self.start_time:
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            return f"{minutes}:{seconds:02d}"
        return "0:00"

    def complete_fight(self, winner_id=None, victory_type=None, details=None):
        """Завершить схватку"""
        if self.status == 'LIVE':
            from models.result import Result

            self.status = 'COMPLETED'
            self.end_time = datetime.utcnow()

            # Если результат уже есть (например, при иппоне), обновляем его
            if self.result:
                self.result.fight_duration = self.duration
                if winner_id:
                    self.result.winner_id = winner_id
                if victory_type:
                    self.result.victory_type = victory_type
                if details:
                    self.result.details = details
            else:
                # Создаем новый результат
                result = Result(
                    fight_id=self.id,
                    winner_id=winner_id,
                    victory_type=victory_type,
                    details=details,
                    fight_duration=self.duration
                )
                db.session.add(result)

            # Добавляем событие завершения боя
            end_event = {
                'id': len(self.events_log) + 1,
                'type': 'SYSTEM',
                'subtype': 'FIGHT_END',
                'description': f'Бой завершен. Победитель: {winner_id} ({victory_type})',
                'match_time': self._get_current_match_time(),
                'timestamp': datetime.utcnow().isoformat(),
                'details': {
                    'winner_id': winner_id,
                    'victory_type': victory_type,
                    'duration': self.duration
                }
            }
            self.events_log.append(end_event)

            self.save()
            return True
        return False

    def reset_fight(self, reason=None):
        """Сбросить схватку для переигровки"""
        if self.status in ['COMPLETED', 'LIVE']:
            # Удаляем результат, если есть
            if self.result:
                db.session.delete(self.result)

            # Сбрасываем статус
            self.status = 'REPLAY'
            self.start_time = None
            self.end_time = None
            self.timer_seconds = self.fight_minutes * 60
            self.is_golden_score = False

            # Очищаем журнал событий
            self.events_log = []

            self.save()
            return True
        return False

    def get_winner(self):
        """Получить победителя"""
        if self.result and self.result.winner_id:
            if self.result.winner_id == self.white_athlete_id:
                return self.white_athlete
            elif self.result.winner_id == self.blue_athlete_id:
                return self.blue_athlete
        return None

    def get_loser(self):
        """Получить проигравшего"""
        winner = self.get_winner()
        if winner:
            if winner.id == self.white_athlete_id:
                return self.blue_athlete
            else:
                return self.white_athlete
        return None

    def to_dict(self):
        """Преобразовать в словарь для API"""
        data = {
            'id': self.id,
            'tournament_id': self.tournament_id,
            'bracket_id': self.bracket_id,
            'category_id': self.category_id,
            'white_athlete_id': self.white_athlete_id,
            'blue_athlete_id': self.blue_athlete_id,
            'tatami': self.tatami,
            'round_number': self.round_number,
            'fight_number': self.fight_number,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'fight_minutes': self.fight_minutes,
            'golden_score_minutes': self.golden_score_minutes,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'timer_seconds': self.timer_seconds,
            'is_golden_score': self.is_golden_score,
            'main_referee': self.main_referee,
            'judge1': self.judge1,
            'judge2': self.judge2,
            'events_log': self.events_log,
            'events_count': len(self.events_log) if self.events_log else 0,
            'duration': self.duration,
            'is_ready_to_start': self.is_ready_to_start,
            'has_active_osaekomi': self.has_active_osaekomi,
            'osaekomi_time': self.osaekomi_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if self.white_athlete:
            data['white_athlete'] = {
                'id': self.white_athlete.id,
                'full_name': self.white_athlete.full_name,
                'club_name': self.white_athlete.club.name if self.white_athlete.club else None
            }

        if self.blue_athlete:
            data['blue_athlete'] = {
                'id': self.blue_athlete.id,
                'full_name': self.blue_athlete.full_name,
                'club_name': self.blue_athlete.club.name if self.blue_athlete.club else None
            }

        if self.result:
            data['result'] = self.result.to_dict()

        return data

    def save(self):
        """Сохранить изменения"""
        try:
            self.updated_at = datetime.utcnow()
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error saving fight: {e}")
            return False

    def save_to_db(self):
        """Алиас для совместимости"""
        return self.save()