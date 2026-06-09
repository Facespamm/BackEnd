from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from models.Enums import AthleteColor, EventType, ScoreType

if TYPE_CHECKING:
    from models.fight_new import FightNew
    from models.new_athlete import AthleteNew


class ScoreEvent(Base):
    __tablename__ = "score_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    fight_id: Mapped[int] = mapped_column(ForeignKey("fights.id", ondelete="CASCADE"))
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"))
    athlete_color: Mapped[AthleteColor] = mapped_column(Enum(AthleteColor))
    event_type: Mapped[EventType] = mapped_column(Enum(EventType))
    score_type: Mapped[Optional[ScoreType]] = mapped_column(
        Enum(ScoreType), default=None
    )
    points: Mapped[int] = mapped_column(default=0)
    technique: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    match_time: Mapped[Optional[int]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Связи
    fight: Mapped["FightNew"] = relationship(back_populates="score_events")
    athlete: Mapped["AthleteNew"] = relationship()
