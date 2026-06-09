from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from models.Enums import RefereeLevels

if TYPE_CHECKING:
    from models.new_associations import FightReferee
    from models.tournament_new import TournamentNew


class RefereeNew(Base):
    __tablename__ = "referees"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    middle_name: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    email: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    phone: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    certification_level: Mapped[Optional[RefereeLevels]] = mapped_column(
        Enum(RefereeLevels), default=None
    )
    tatami_assigned: Mapped[Optional[int]] = mapped_column(default=None)

    # связи
    fight_referees: Mapped[List["FightReferee"]] = relationship(
        back_populates="referees", passive_deletes=True
    )
    tournament: Mapped[List["TournamentNew"]] = relationship(
        back_populates="chief_referee", passive_deletes=True
    )
