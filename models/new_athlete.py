from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base

if TYPE_CHECKING:
    from models.AthleteTournamentRegistration import AthleteTournamentRegistration
    from models.category_new import CategoryNew
    from models.fight_new import FightNew
    from models.new_associations import AthleteRegistration
    from models.new_club import ClubNew
    from models.new_dan import DanNew
    from models.new_user import UserNew
    from models.weighing_new import WeighingNew


class AthleteNew(Base):
    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), default=None
    )
    club_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("clubs.id", ondelete="SET NULL"), default=None
    )
    birth_date: Mapped[date] = mapped_column(Date)
    gender: Mapped[str] = mapped_column(String(10))
    age: Mapped[int] = mapped_column()
    rank_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dans.id"), default=None)
    license_number: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    medical_check: Mapped[bool] = mapped_column(Boolean, default=False)
    insurance_number: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    rank: Mapped[Optional["DanNew"]] = relationship()
    club: Mapped[Optional["ClubNew"]] = relationship(back_populates="athletes")
    user: Mapped["UserNew"] = relationship(back_populates="athlete_profile")
    weighings: Mapped[List["WeighingNew"]] = relationship(
        back_populates="athlete", cascade="all, delete-orphan"
    )
    registrations: Mapped[List["AthleteRegistration"]] = relationship(
        back_populates="athlete", cascade="all, delete-orphan"
    )
    white_fights: Mapped[List["FightNew"]] = relationship(
        back_populates="white_athlete", foreign_keys="FightNew.white_athlete_id"
    )
    blue_fights: Mapped[List["FightNew"]] = relationship(
        back_populates="blue_athlete", foreign_keys="FightNew.blue_athlete_id"
    )
    categories: Mapped[List["CategoryNew"]] = relationship(back_populates="athletes")
    athlete_tournament_registration: Mapped[List["AthleteTournamentRegistration"]] = (
        relationship(back_populates="athlete")
    )
