from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base

if TYPE_CHECKING:
    from models.category_new import CategoryNew
    from models.fight_new import FightNew
    from models.new_athlete import AthleteNew
    from models.new_referee import RefereeNew
    from models.tournament_new import TournamentNew
    from models.weighing_new import WeighingNew

new_user_roles = Table(
    "new_user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)


class TournamentCategory(Base):
    __tablename__ = "new_tournament_categories"

    tournament_category_id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE")
    )
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    has_consolidation_fights: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    tournament: Mapped["TournamentNew"] = relationship(
        back_populates="tournament_categories"
    )
    category: Mapped["CategoryNew"] = relationship(
        back_populates="tournament_categories"
    )
    registrations: Mapped[List["AthleteRegistration"]] = relationship(
        back_populates="tournament_categories"
    )
    weighings: Mapped[List["WeighingNew"]] = relationship(
        back_populates="tournament_categories"
    )


class AthleteRegistration(Base):
    __tablename__ = "new_athlete_tournament"

    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"))
    tournament_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "new_tournament_categories.tournament_category_id", ondelete="SET NULL"
        ),
        default=None,
    )
    registration_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Relationships
    athlete: Mapped["AthleteNew"] = relationship(back_populates="registrations")
    tournament_categories: Mapped["TournamentCategory"] = relationship(
        back_populates="registrations"
    )


class FightReferee(Base):
    __tablename__ = "fight_referee"

    id: Mapped[int] = mapped_column(primary_key=True)
    fight_id: Mapped[int] = mapped_column(ForeignKey("fights.id"))
    referee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("referees.id", ondelete="SET NULL"), default=None
    )
    role: Mapped[Optional[str]] = mapped_column(String(20), default=None)

    # Relationships
    fight: Mapped["FightNew"] = relationship(back_populates="fight_referees")
    referees: Mapped["RefereeNew"] = relationship(back_populates="fight_referees")
