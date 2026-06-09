from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from models.Enums import VictoryType

if TYPE_CHECKING:
    from models.fight_new import FightNew
    from models.new_athlete import AthleteNew


class ResultNew(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(primary_key=True)
    fight_id: Mapped[int] = mapped_column(ForeignKey("fights.id", ondelete="CASCADE"))
    winner_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"))
    victory_type: Mapped[VictoryType] = mapped_column(Enum(VictoryType))
    fight_duration: Mapped[int] = mapped_column()
    count_of_fights_win: Mapped[int] = mapped_column(default=0)

    # связи
    fight: Mapped["FightNew"] = relationship(back_populates="result")
    winner: Mapped[Optional["AthleteNew"]] = relationship()
