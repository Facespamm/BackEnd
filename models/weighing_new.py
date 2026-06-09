from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base

if TYPE_CHECKING:
    from models.category_new import CategoryNew
    from models.new_associations import TournamentCategory
    from models.new_athlete import AthleteNew


class WeighingNew(Base):
    __tablename__ = "weighings"

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_category_id: Mapped[int] = mapped_column(
        ForeignKey(
            "new_tournament_categories.tournament_category_id", ondelete="CASCADE"
        )
    )
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"))
    weight: Mapped[float] = mapped_column(Float)
    weight_category: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, default=None)
    weighing_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Связи
    tournament_categories: Mapped["TournamentCategory"] = relationship(
        back_populates="weighings"
    )
    athlete: Mapped["AthleteNew"] = relationship(back_populates="weighings")
    category: Mapped["CategoryNew"] = relationship(back_populates="weighings")
