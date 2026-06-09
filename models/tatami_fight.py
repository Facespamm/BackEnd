from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from models.Enums import TatamiStatus

if TYPE_CHECKING:
    from models.fight_new import FightNew
    from models.tournament_new import TournamentNew


class TatamiFight(Base):
    __tablename__ = "tatami_fight"

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE")
    )
    tatami_number: Mapped[int] = mapped_column()
    fight_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("fights.id"), default=None
    )
    status: Mapped[TatamiStatus] = mapped_column(
        Enum(TatamiStatus), default=TatamiStatus.FREE
    )

    # Связи
    fight: Mapped[Optional["FightNew"]] = relationship(
        back_populates="tatami_fight", uselist=False
    )
    tournament: Mapped["TournamentNew"] = relationship(back_populates="tatami_fight")
