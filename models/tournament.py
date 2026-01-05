from datetime import datetime
from databse.db import db, create_session
from models.associations import athlete_tournament
from models.fight import Fight

class Tournament(db.Model):
    """
    Модель турнира
    """
    __tablename__ = 'tournaments'

    # Основная информация
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    # Даты проведения
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    registration_deadline = db.Column(db.Date)

    # Место проведения
    venue = db.Column(db.String(200))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    country = db.Column(db.String(50), default='Россия')

    # Настройки турнира
    max_athletes = db.Column(db.Integer, default=0)  # 0 = без ограничений
    tatami_count = db.Column(db.Integer, default=1)
    fight_duration = db.Column(db.Integer, default=300)  # в секундах
    golden_score_duration = db.Column(db.Integer, default=180)  # в секундах

    # Статус турнира
    status = db.Column(db.String(20), default='PLANNED')  # PLANNED, REGISTRATION, WEIGHING, BRACKETS, LIVE, COMPLETED, CANCELLED
    is_public = db.Column(db.Boolean, default=True)

    # Организационная информация
    organizer = db.Column(db.String(100))
    chief_referee = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(100))

    # Связи
    categories = db.relationship('Category', back_populates='tournament', lazy=True, cascade='all, delete-orphan')
    fights = db.relationship('Fight', back_populates='tournament', lazy=True)
    brackets = db.relationship('Bracket', back_populates='tournament')
    referees = db.relationship('Referee', secondary='referee_tournament', back_populates='tournaments')

    def __repr__(self):
        return f'<Tournament {self.name}>'

    @property
    def duration_days(self):
        """Количество дней турнира"""
        return (self.end_date - self.start_date).days + 1

    @property
    def is_registration_open(self):
        """Открыта ли регистрация"""
        if self.registration_deadline:
            return datetime.now().date() <= self.registration_deadline
        return self.status in ['PLANNED', 'REGISTRATION']

    @property
    def athletes_count(self):
        """Количество зарегистрированных участников"""
        from models.category import Category
        total = 0
        for category in self.categories:
            total += category.athletes_count
        return total

    @property
    def completed_fights_count(self):
        """Количество завершенных схваток"""
        from models.fight import Fight
        return Fight.query.filter_by(
            tournament_id=self.id,
            status='COMPLETED'
        ).count()

    @property
    def total_fights_count(self):
        """Общее количество схваток"""
        return Fight.query.filter_by(tournament_id=self.id).count()

    @property
    def progress_percentage(self):
        """Процент завершения турнира"""
        if self.total_fights_count == 0:
            return 0
        return int((self.completed_fights_count / self.total_fights_count) * 100)

    def get_categories_by_gender(self, gender):
        """Получить категории по полу"""
        return [cat for cat in self.categories if cat.gender == gender]

    def get_live_fights(self):
        """Получить активные схватки"""
        from models.fight import Fight
        return Fight.query.filter_by(
            tournament_id=self.id,
            status='LIVE'
        ).all()

    def get_todays_fights(self):
        """Получить схватки на сегодня"""
        from models.fight import Fight
        today = datetime.now().date()
        return Fight.query.filter(
            Fight.tournament_id == self.id,
            db.func.date(Fight.scheduled_time) == today
        ).all()

    def save_to_db(self):
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(e)  # или логгируй
            return False