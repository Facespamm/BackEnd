from datetime import datetime
from databse.db import db

class Bracket(db.Model):
    """
    Модель турнирной сетки
    """
    __tablename__ = 'brackets'

    # Связи
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

    # Информация о сетке
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    name = db.Column(db.String(100), nullable=False)
    bracket_type = db.Column(db.String(20), default='SINGLE_ELIMINATION')  # SINGLE_ELIMINATION, DOUBLE_ELIMINATION, ROUND_ROBIN
    status = db.Column(db.String(20), default='CREATED')  # CREATED, GENERATED, LIVE, COMPLETED

    # Настройки
    has_consolation = db.Column(db.Boolean, default=True)  # Утешительные схватки за 3 место
    max_rounds = db.Column(db.Integer, default=0)  # 0 = автоматически

    # Связи
    fights = db.relationship('Fight', backref='bracket', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Bracket {self.name}>'

    @property
    def athletes_count(self):
        """Количество участников в сетке"""
        return len(self.category.athletes)

    @property
    def completed_fights_count(self):
        """Количество завершенных схваток"""
        return len([f for f in self.fights if f.status == 'COMPLETED'])

    @property
    def total_fights_count(self):
        """Общее количество схваток"""
        return len(self.fights)

    @property
    def progress_percentage(self):
        """Процент завершения сетки"""
        if self.total_fights_count == 0:
            return 0
        return int((self.completed_fights_count / self.total_fights_count) * 100)

    @property
    def current_round(self):
        """Текущий активный раунд"""
        live_fights = [f for f in self.fights if f.status == 'LIVE']
        if live_fights:
            return live_fights[0].round_number

        scheduled_fights = [f for f in self.fights if f.status == 'SCHEDULED']
        if scheduled_fights:
            return min(f.round_number for f in scheduled_fights)

        return 0

    @property
    def winner(self):
        """Победитель сетки"""
        if self.status != 'COMPLETED':
            return None

        # Ищем финальную схватку
        final_fight = Fight.query.filter_by(
            bracket_id=self.id,
            round_number=1
        ).first()

        if final_fight and final_fight.result:
            return final_fight.result.winner
        return None

    @property
    def third_place(self):
        """Третье место (если есть утешительные)"""
        if not self.has_consolation or self.status != 'COMPLETED':
            return None

        # Ищем схватку за 3 место
        third_place_fight = Fight.query.filter_by(
            bracket_id=self.id,
            round_number=2  # Обычно второй раунд в утешительных
        ).order_by(Fight.fight_number.desc()).first()

        if third_place_fight and third_place_fight.result:
            return third_place_fight.result.winner
        return None

    def get_round_fights(self, round_number):
        """Получить схватки определенного раунда"""
        return [f for f in self.fights if f.round_number == round_number]

    def get_live_fights(self):
        """Получить активные схватки"""
        return [f for f in self.fights if f.status == 'LIVE']

    def get_scheduled_fights(self):
        """Получить запланированные схватки"""
        return [f for f in self.fights if f.status == 'SCHEDULED']

    def get_completed_fights(self):
        """Получить завершенные схватки"""
        return [f for f in self.fights if f.status == 'COMPLETED']

    def get_athlete_fights(self, athlete_id):
        """Получить все схватки участника в этой сетке"""
        return [f for f in self.fights 
                if (f.white_athlete_id == athlete_id or f.blue_athlete_id == athlete_id)]

    def generate_fights(self):
        """Генерирует схватки для сетки"""
        from services.bracket_generator import BracketGenerator
        generator = BracketGenerator(self)
        return generator.generate()

    def get_standings(self):
        """Получить текущее положение участников"""
        standings = []

        for athlete in self.category.athletes:
            fights = self.get_athlete_fights(athlete.id)
            victories = len([f for f in fights if f.result and f.result.winner_id == athlete.id])
            defeats = len([f for f in fights if f.result and f.result.winner_id != athlete.id])

            standings.append({
                'athlete': athlete,
                'fights_count': len(fights),
                'victories': victories,
                'defeats': defeats,
                'position': None  # Будет определено после завершения
            })

        # Сортируем по количеству побед
        standings.sort(key=lambda x: x['victories'], reverse=True)

        # Определяем позиции
        for i, standing in enumerate(standings):
            standing['position'] = i + 1

        return standings

    def save_to_db(self):
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(e)
            return False