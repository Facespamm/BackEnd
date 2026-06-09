from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Interval
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from models.Enums import BracketType, FightStatus

if TYPE_CHECKING:
    from models.new_associations import FightReferee
    from models.new_athlete import AthleteNew
    from models.result_new import ResultNew
    from models.score_event import ScoreEvent
    from models.tatami_fight import TatamiFight


class FightNew(Base):
    __tablename__ = "fights"

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_category_id: Mapped[int] = mapped_column(
        ForeignKey(
            "new_tournament_categories.tournament_category_id", ondelete="CASCADE"
        )
    )
    white_athlete_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("athletes.id"), default=None
    )
    blue_athlete_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("athletes.id"), default=None
    )

    # Информация о схватке
    tatami_number: Mapped[int] = mapped_column(default=0)
    round_number: Mapped[int] = mapped_column(default=1)
    fight_number: Mapped[Optional[int]] = mapped_column(default=None)

    # Статус схватки
    status: Mapped[FightStatus] = mapped_column(
        Enum(FightStatus), default=FightStatus.SCHEDULED
    )
    start_time: Mapped[Optional[timedelta]] = mapped_column(Interval, default=None)
    end_time: Mapped[Optional[timedelta]] = mapped_column(Interval, default=None)
    next_fight_id: Mapped[Optional[int]] = mapped_column(default=None)
    type_bracket: Mapped[BracketType] = mapped_column(
        Enum(BracketType), default=BracketType.MAIN
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Связи
    white_athlete: Mapped[Optional["AthleteNew"]] = relationship(
        back_populates="white_fights", foreign_keys="FightNew.white_athlete_id"
    )
    blue_athlete: Mapped[Optional["AthleteNew"]] = relationship(
        back_populates="blue_fights", foreign_keys="FightNew.blue_athlete_id"
    )
    fight_referees: Mapped[List["FightReferee"]] = relationship(back_populates="fight")
    score_events: Mapped[List["ScoreEvent"]] = relationship(
        back_populates="fight", cascade="all, delete-orphan"
    )
    result: Mapped[Optional["ResultNew"]] = relationship(
        back_populates="fight", uselist=False, cascade="all, delete-orphan"
    )
    tatami_fight: Mapped[Optional["TatamiFight"]] = relationship(
        back_populates="fight", uselist=False
    )
