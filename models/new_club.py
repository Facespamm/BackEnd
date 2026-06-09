from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base

if TYPE_CHECKING:
    from models.new_athlete import AthleteNew


class ClubNew(Base):
    __tablename__ = "clubs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    short_name: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    country: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    city: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    address: Mapped[Optional[str]] = mapped_column(Text, default=None)
    phone: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    email: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    website: Mapped[Optional[str]] = mapped_column(String(200), default=None)
    coach_name: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    founded_year: Mapped[Optional[int]] = mapped_column(default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # связи
    athletes: Mapped[List["AthleteNew"]] = relationship(back_populates="club")
