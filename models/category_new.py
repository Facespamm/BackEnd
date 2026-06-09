from datetime import datetime
from typing import List, Optional

from database.db import Base
from sqlalchemy import Boolean, DateTime, Enum, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing_extensions import TYPE_CHECKING

from models.Enums import Gender

if TYPE_CHECKING:
    from models.new_associations import TournamentCategory
    from models.new_athlete import AthleteNew
    from models.weighing_new import WeighingNew


class CategoryNew(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    gender: Mapped[Gender] = mapped_column(Enum(Gender))
    min_weight: Mapped[Optional[float]] = mapped_column(Float, default=None)
    max_weight: Mapped[Optional[float]] = mapped_column(Float, default=None)
    min_year: Mapped[Optional[int]] = mapped_column(default=None)
    max_year: Mapped[Optional[int]] = mapped_column(default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # связи
    tournament_categories: Mapped[List["TournamentCategory"]] = relationship(
        back_populates="category"
    )
    weighings: Mapped[List["WeighingNew"]] = relationship(back_populates="category")
    athletes: Mapped[List["AthleteNew"]] = relationship(back_populates="categories")
