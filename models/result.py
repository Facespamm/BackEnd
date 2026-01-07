from datetime import datetime

from config import VICTORY_TYPES, SCORE_VALUES, OSAEKOMI_TIMES, MAX_PENALTIES
from databse.db import db


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
    winner_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=True)
    # Результат
    victory_type = db.Column(db.String(30), nullable=True)  # IPPON, WAZAARI, SHIDO, etc.
    details = db.Column(db.Text)  # Дополнительная информация

    # Счет
    white_score = db.Column(db.Integer, default=0)  # Общий счет белого
    blue_score = db.Column(db.Integer, default=0)  # Общий счет синего

    # Детализированные оценки
    white_yuko = db.Column(db.Integer, default=0)  # Количество ЮКО у белого
    blue_yuko = db.Column(db.Integer, default=0)  # Количество ЮКО у синего
    white_wazaari = db.Column(db.Integer, default=0)  # Количество ВАЗА-АРИ у белого
    blue_wazaari = db.Column(db.Integer, default=0)  # Количество ВАЗА-АРИ у синего
    white_ippon = db.Column(db.Integer, default=0)  # Количество ИППОН у белого
    blue_ippon = db.Column(db.Integer, default=0)  # Количество ИППОН у синего

    # Штрафы
    white_penalties = db.Column(db.String(100))  # Штрафы белого (например: "SHIDO,SHIDO")
    blue_penalties = db.Column(db.String(100))  # Штрафы синего

    # Осаекоми
    osaekomi_start_time = db.Column(db.DateTime)  # Время начала удержания
    osaekomi_athlete_color = db.Column(db.String(10))  # Цвет атакующего (WHITE/BLUE)
    osaekomi_duration = db.Column(db.Integer, default=0)  # Общее время осаекоми в секундах

    # Технические действия
    technique_used = db.Column(db.String(100))  # Использованная техника
    is_ippon = db.Column(db.Boolean, default=False)
    is_wazaari = db.Column(db.Boolean, default=False)

    # Связи
    winner = db.relationship('Athlete', foreign_keys=[winner_id])
    fight = db.relationship('Fight', back_populates='result')

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
        return VICTORY_TYPES.get(self.victory_type, self.victory_type)

    @property
    def scores_summary(self):
        """Сводка по оценкам"""
        summary = []

        if self.white_yuko > 0:
            summary.append(f"Белый: {self.white_yuko} ЮКО")
        if self.white_wazaari > 0:
            summary.append(f"Белый: {self.white_wazaari} ВАЗА-АРИ")
        if self.white_ippon > 0:
            summary.append(f"Белый: {self.white_ippon} ИППОН")

        if self.blue_yuko > 0:
            summary.append(f"Синий: {self.blue_yuko} ЮКО")
        if self.blue_wazaari > 0:
            summary.append(f"Синий: {self.blue_wazaari} ВАЗА-АРИ")
        if self.blue_ippon > 0:
            summary.append(f"Синий: {self.blue_ippon} ИППОН")

        return "; ".join(summary)

    @property
    def osaekomi_time(self):
        """Текущее время удержания (если активно)"""
        if self.osaekomi_start_time:
            return int((datetime.utcnow() - self.osaekomi_start_time).total_seconds())
        return 0

    def add_score(self, athlete_color, score_type, technique=None):
        """Добавить оценку (ЮКО, ВАЗА-АРИ, ИППОН)"""
        # Внутреннее действие без логирования в result
        score_value = SCORE_VALUES.get(score_type.upper(), 0)

        if athlete_color.upper() == 'WHITE':
            self.white_score += score_value

            if score_type.upper() == 'YUKO':
                self.white_yuko += 1
            elif score_type.upper() == 'WAZAARI':
                self.white_wazaari += 1
                self.is_wazaari = True
            elif score_type.upper() == 'IPPON':
                self.white_ippon += 1
                self.is_ippon = True
                self.victory_type = 'IPPON'
        else:
            self.blue_score += score_value

            if score_type.upper() == 'YUKO':
                self.blue_yuko += 1
            elif score_type.upper() == 'WAZAARI':
                self.blue_wazaari += 1
                self.is_wazaari = True
            elif score_type.upper() == 'IPPON':
                self.blue_ippon += 1
                self.is_ippon = True
                self.victory_type = 'IPPON'

        if technique:
            self.technique_used = technique

        # Проверяем условие победы по 2 ВАЗА-АРИ
        if self.white_wazaari >= 2:
            self.victory_type = 'WAZAARI_AWASETE_IPPON'
            if self.fight:
                self.winner_id = self.fight.white_athlete_id
        elif self.blue_wazaari >= 2:
            self.victory_type = 'WAZAARI_AWASETE_IPPON'
            if self.fight:
                self.winner_id = self.fight.blue_athlete_id

        # Возвращаем информацию для ScoreManager
        return {
            'type': 'score',
            'athlete_color': athlete_color.upper(),
            'score_type': score_type.upper(),
            'technique': technique,
            'points': score_value,
            'white_score': self.white_score,
            'blue_score': self.blue_score
        }

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

        # Проверяем автоматическую победу по штрафам
        white_count = self.get_penalty_count('WHITE')
        blue_count = self.get_penalty_count('BLUE')

        if white_count >= MAX_PENALTIES['SHIDO']:
            self.victory_type = 'SHIDO'
            if self.fight and self.fight.blue_athlete_id:
                self.winner_id = self.fight.blue_athlete_id
        elif blue_count >= MAX_PENALTIES['SHIDO']:
            self.victory_type = 'SHIDO'
            if self.fight and self.fight.white_athlete_id:
                self.winner_id = self.fight.white_athlete_id

        # Возвращаем информацию для ScoreManager
        return {
            'type': 'penalty',
            'athlete_color': athlete_color.upper(),
            'penalty_type': penalty_type.upper(),
            'white_penalties': self.white_penalties,
            'blue_penalties': self.blue_penalties
        }

    def start_osaekomi(self, athlete_color):
        """Начать отсчет времени удержания"""
        self.osaekomi_start_time = datetime.utcnow()
        self.osaekomi_athlete_color = athlete_color.upper()

        # Возвращаем информацию для ScoreManager
        return {
            'type': 'osaekomi_start',
            'athlete_color': athlete_color.upper(),
            'start_time': self.osaekomi_start_time
        }

    def stop_osaekomi(self):
        """Остановить отсчет времени удержания"""
        if self.osaekomi_start_time and self.osaekomi_athlete_color:
            duration = int((datetime.utcnow() - self.osaekomi_start_time).total_seconds())
            self.osaekomi_duration += duration

            # Начисляем оценку в зависимости от времени удержания
            awarded_score = None
            if duration >= OSAEKOMI_TIMES['IPPON']:
                awarded_score = 'IPPON'
                self.add_score(self.osaekomi_athlete_color, 'IPPON', technique='OSAEKOMI')
            elif duration >= OSAEKOMI_TIMES['WAZAARI']:
                awarded_score = 'WAZAARI'
                self.add_score(self.osaekomi_athlete_color, 'WAZAARI', technique='OSAEKOMI')

            previous_athlete_color = self.osaekomi_athlete_color
            self.osaekomi_start_time = None
            self.osaekomi_athlete_color = None

            return {
                'duration': duration,
                'awarded_score': awarded_score,
                'athlete_color': previous_athlete_color,
                'white_score': self.white_score,
                'blue_score': self.blue_score
            }
        return None

    def get_penalty_count(self, athlete_color):
        """Получить количество штрафов участника"""
        if athlete_color.upper() == 'WHITE':
            return len(self.white_penalties.split(',')) if self.white_penalties else 0
        else:
            return len(self.blue_penalties.split(',')) if self.blue_penalties else 0

    def undo_last_action(self):
        """Отменить последнее действие - ЗАГЛУШКА"""
        # Теперь этот метод НЕ РАБОТАЕТ, потому что логирование
        # перенесено в ScoreManager и fight.events_log
        # Вся логика отмены теперь в ScoreManager.undo_last_action()
        return False, None

    def reset_scores(self):
        """Сбросить все оценки и штрафы"""
        self.white_score = 0
        self.blue_score = 0
        self.white_yuko = 0
        self.blue_yuko = 0
        self.white_wazaari = 0
        self.blue_wazaari = 0
        self.white_ippon = 0
        self.blue_ippon = 0
        self.white_penalties = None
        self.blue_penalties = None
        self.osaekomi_start_time = None
        self.osaekomi_athlete_color = None
        self.osaekomi_duration = 0
        self.is_ippon = False
        self.is_wazaari = False
        self.victory_type = None
        self.winner_id = None
        self.technique_used = None

    def to_dict(self):
        """Преобразовать в словарь для API"""
        data = {
            'id': self.id,
            'fight_id': self.fight_id,
            'winner_id': self.winner_id,
            'victory_type': self.victory_type,
            'victory_description': self.victory_description,
            'details': self.details,
            'white_score': self.white_score,
            'blue_score': self.blue_score,
            'white_yuko': self.white_yuko,
            'blue_yuko': self.blue_yuko,
            'white_wazaari': self.white_wazaari,
            'blue_wazaari': self.blue_wazaari,
            'white_ippon': self.white_ippon,
            'blue_ippon': self.blue_ippon,
            'white_penalties': self.white_penalties,
            'blue_penalties': self.blue_penalties,
            'white_penalty_count': self.get_penalty_count('WHITE'),
            'blue_penalty_count': self.get_penalty_count('BLUE'),
            'fight_duration': self.fight_duration,
            'golden_score_time': self.golden_score_time,
            'technique_used': self.technique_used,
            'is_ippon': self.is_ippon,
            'is_wazaari': self.is_wazaari,
            'is_quick_victory': self.is_quick_victory,
            'penalties_summary': self.penalties_summary,
            'scores_summary': self.scores_summary,
            'osaekomi_active': self.osaekomi_start_time is not None,
            'osaekomi_athlete_color': self.osaekomi_athlete_color,
            'osaekomi_time': self.osaekomi_time,
            'osaekomi_duration': self.osaekomi_duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if self.winner:
            data['winner_name'] = self.winner.full_name
            data['winner_club'] = self.winner.club.name if self.winner.club else None

        return data

    def save_to_db(self):
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error saving result: {e}")
            return False