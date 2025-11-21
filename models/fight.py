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
    status = db.Column(db.String(20), default='SCHEDULED')  # SCHEDULED, LIVE, COMPLETED, CANCELLED
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

    # Таймер
    timer_seconds = db.Column(db.Integer, default=0)
    is_golden_score = db.Column(db.Boolean, default=False)
    timer_paused = db.Column(db.Boolean, default=True)

    # Судьи
    main_referee = db.Column(db.String(100))
    judge1 = db.Column(db.String(100))
    judge2 = db.Column(db.String(100))

    # Связи
    result = db.relationship('Result', backref='fight', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Fight {self.fight_number} - Round {self.round_number}>'

    @property
    def duration(self):
        """Длительность схватки"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

    @property
    def is_ready_to_start(self):
        """Готова ли схватка к началу"""
        return (self.white_athlete_id is not None and 
                self.blue_athlete_id is not None and 
                self.status == 'SCHEDULED')

    @property
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
            self.timer_seconds = self.tournament.fight_duration
            self.timer_paused = False
            self.save()
            return True
        return False

    def pause_fight(self):
        """Приостановить схватку"""
        if self.status == 'LIVE':
            self.timer_paused = True
            self.save()
            return True
        return False

    def resume_fight(self):
        """Возобновить схватку"""
        if self.status == 'LIVE' and self.timer_paused:
            self.timer_paused = False
            self.save()
            return True
        return False

    def enter_golden_score(self):
        """Перейти в золотой скор"""
        if self.status == 'LIVE' and self.timer_seconds <= 0:
            self.is_golden_score = True
            self.timer_seconds = self.tournament.golden_score_duration
            self.timer_paused = False
            self.save()
            return True
        return False

    def complete_fight(self, winner_id, victory_type, details=None):
        """Завершить схватку"""
        if self.status == 'LIVE':
            from models.result import Result

            self.status = 'COMPLETED'
            self.end_time = datetime.utcnow()

            # Создаем результат
            result = Result(
                fight_id=self.id,
                winner_id=winner_id,
                victory_type=victory_type,
                details=details,
                fight_duration=self.duration
            )

            db.session.add(result)
            self.save()
            return True
        return False

    def get_winner(self):
        """Получить победителя"""
        if self.result:
            return self.result.winner
        return None

    def get_loser(self):
        """Получить проигравшего"""
        if self.result:
            if self.result.winner_id == self.white_athlete_id:
                return self.blue_athlete
            else:
                return self.white_athlete
        return None

    def to_dict(self):
        """Преобразовать в словарь для API"""
        data = super().to_dict()
        data['white_athlete'] = self.white_athlete.full_name if self.white_athlete else None
        data['blue_athlete'] = self.blue_athlete.full_name if self.blue_athlete else None
        data['result'] = self.result.to_dict() if self.result else None
        return data