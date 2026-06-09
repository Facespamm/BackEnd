from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from models.Enums import StatusTournament

if TYPE_CHECKING:
    from models.AthleteTournamentRegistration import AthleteTournamentRegistration
    from models.new_associations import TournamentCategory
    from models.new_referee import RefereeNew
    from models.tatami_fight import TatamiFight


class TournamentNew(Base):
    """
    Модель турнира
    """

    __tablename__ = "tournaments"

    # Основная информация
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)

    # Даты проведения
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    registration_deadline: Mapped[Optional[date]] = mapped_column(Date, default=None)

    # Место проведения
    venue: Mapped[Optional[str]] = mapped_column(String(200), default=None)
    address: Mapped[Optional[str]] = mapped_column(Text, default=None)
    city: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    country: Mapped[str] = mapped_column(String(50), default="Россия")

    # Настройки турнира
    max_athletes: Mapped[int] = mapped_column(default=0)
    tatami_count: Mapped[int] = mapped_column(default=1)
    fight_duration: Mapped[int] = mapped_column(default=300)
    golden_score_duration: Mapped[int] = mapped_column(default=180)

    # Статус турнира
    status: Mapped[StatusTournament] = mapped_column(
        Enum(StatusTournament), default=StatusTournament.PLANNED
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    has_consolation_fights: Mapped[bool] = mapped_column(Boolean, default=False)

    # Организационная информация
    organizer: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    chief_referee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("referees.id"), default=None
    )
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    contact_email: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Связи
    tournament_categories: Mapped[List["TournamentCategory"]] = relationship(
        back_populates="tournament", cascade="all, delete-orphan"
    )
    chief_referee: Mapped[Optional["RefereeNew"]] = relationship(
        back_populates="tournament"
    )
    tatami_fight: Mapped[List["TatamiFight"]] = relationship(
        back_populates="tournament", cascade="all, delete-orphan"
    )
    registrations: Mapped[List["AthleteTournamentRegistration"]] = relationship(
        back_populates="tournament", cascade="all, delete-orphan"
    )
