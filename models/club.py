from database.db import db
from models.base import BaseModel

class Club(BaseModel):
    """
    Модель клуба/команды
    """
    __tablename__ = 'clubs'

    # Основная информация
    name = db.Column(db.String(100), nullable=False, unique=True)
    short_name = db.Column(db.String(20))
    city = db.Column(db.String(50))
    country = db.Column(db.String(50), default='Россия')

    # Контактная информация
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    website = db.Column(db.String(200))

    # Дополнительная информация
    coach_name = db.Column(db.String(100))
    founded_year = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Club {self.name}>'

    @property
    def athletes_count(self):
        """Количество активных спортсменов в клубе"""
        return len([a for a in self.athletes if a.is_active])

    def get_tournament_results(self, tournament_id):
        """Получить результаты клуба в турнире"""
        from models.result import Result
        from models.fight import Fight

        victories = db.session.query(Result).join(Fight).filter(
            Fight.tournament_id == tournament_id,
            Result.winner.has(club_id=self.id)
        ).count()

        return {
            'victories': victories,
            'athletes_count': len([a for a in self.athletes if a.is_active])
        }