from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing_extensions import TYPE_CHECKING

from database.db import Base
from models.Enums import StatusTournamentRegistration

if TYPE_CHECKING:
    from models.new_athlete import AthleteNew
    from models.tournament_new import TournamentNew


class AthleteTournamentRegistration(Base):
    __tablename__ = "athlete_tournament_registration"

    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"))
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE")
    )
    registration_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC)
    )
    status: Mapped[StatusTournamentRegistration] = mapped_column(
        Enum(StatusTournamentRegistration),
        default=StatusTournamentRegistration.REGISTERED,
    )
    registered_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), default=None
    )

    # Relationships
    athlete: Mapped["AthleteNew"] = relationship(
        back_populates="athlete_tournament_registration"
    )
    tournament: Mapped["TournamentNew"] = relationship(back_populates="registrations")
