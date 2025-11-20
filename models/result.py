from datetime import datetime
from database.db import db

class Result(db.Model):
    """
    Модель результата схватки
    """
    __tablename__ = 'results'

    # Связи
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fight_id = db.Column(db.Integer, db.ForeignKey('fights.id'), nullable=False, unique=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=False)

    # Результат
    victory_type = db.Column(db.String(30), nullable=False)  # IPPON, WAZAARI, SHIDO, etc.
    details = db.Column(db.Text)  # Дополнительная информация

    # Счет
    white_score = db.Column(db.Integer, default=0)  # Очки белого
    blue_score = db.Column(db.Integer, default=0)   # Очки синего

    # Штрафы
    white_penalties = db.Column(db.String(100))  # Штрафы белого (например: "SHIDO,SHIDO")
    blue_penalties = db.Column(db.String(100))   # Штрафы синего

    # Время
    fight_duration = db.Column(db.Integer)  # Длительность в секундах
    golden_score_time = db.Column(db.Integer)  # Время в золотом скоре

    # Технические действия
    technique_used = db.Column(db.String(100))  # Использованная техника
    is_ippon = db.Column(db.Boolean, default=False)
    is_wazaari = db.Column(db.Boolean, default=False)

    # Связи
    winner = db.relationship('Athlete', foreign_keys=[winner_id])

    def __repr__(self):
        return f'<Result Fight#{self.fight_id} Winner: {self.winner_id}>'

    @property
    def is_quick_victory(self):
        """Быстрая победа (менее 1 минуты)"""
        return self.fight_duration and self.fight_duration < 60

    @property
    def penalties_summary(self):
        """Сводка по штрафам"""
        summary = []

        if self.white_penalties:
            white_count = len(self.white_penalties.split(','))
            summary.append(f"Белый: {white_count} штрафов")

        if self.blue_penalties:
            blue_count = len(self.blue_penalties.split(','))
            summary.append(f"Синий: {blue_count} штрафов")

        return ", ".join(summary)

    @property
    def victory_description(self):
        """Описание типа победы"""
        from config import Config
        return Config.VICTORY_TYPES.get(self.victory_type, self.victory_type)

    def add_penalty(self, athlete_color, penalty_type):
        """Добавить штраф участнику"""
        if athlete_color.upper() == 'WHITE':
            current = self.white_penalties or ""
            penalties = current.split(',') if current else []
            penalties.append(penalty_type)
            self.white_penalties = ','.join(penalties)
        else:
            current = self.blue_penalties or ""
            penalties = current.split(',') if current else []
            penalties.append(penalty_type)
            self.blue_penalties = ','.join(penalties)

        # Автоматическая победа по штрафам
        white_count = len(self.white_penalties.split(',')) if self.white_penalties else 0
        blue_count = len(self.blue_penalties.split(',')) if self.blue_penalties else 0

        if white_count >= 3:
            self.victory_type = 'SHIDO'
            self.winner_id = self.fight.blue_athlete_id
        elif blue_count >= 3:
            self.victory_type = 'SHIDO'
            self.winner_id = self.fight.white_athlete_id

    def get_penalty_count(self, athlete_color):
        """Получить количество штрафов участника"""
        if athlete_color.upper() == 'WHITE':
            return len(self.white_penalties.split(',')) if self.white_penalties else 0
        else:
            return len(self.blue_penalties.split(',')) if self.blue_penalties else 0

    def to_dict(self):
        """Преобразовать в словарь для API"""
        data = super().to_dict()
        data['winner_name'] = self.winner.full_name if self.winner else None
        data['victory_description'] = self.victory_description
        data['white_penalty_count'] = self.get_penalty_count('WHITE')
        data['blue_penalty_count'] = self.get_penalty_count('BLUE')
        return data