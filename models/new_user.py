from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from database.db import Base
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.new_associations import new_user_roles

if TYPE_CHECKING:
    from models.new_athlete import AthleteNew
    from models.role_new import RoleNew


class UserNew(Base):
    """
    Модель пользователя системы
    """

    __tablename__ = "users"

    # Учетные данные
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    # Информация о пользователе
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    middle_name: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    email: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    phone: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Связи
    athlete_profile: Mapped[List["AthleteNew"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    roles: Mapped[List["RoleNew"]] = relationship(
        secondary=new_user_roles, back_populates="users"
    )
