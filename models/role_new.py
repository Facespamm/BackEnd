from typing import TYPE_CHECKING, List

from database.db import Base
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.new_associations import new_user_roles

if TYPE_CHECKING:
    from models.new_user import UserNew


class RoleNew(Base):
    """Модель роли пользователя"""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    normalized_name: Mapped[str] = mapped_column(String(50), unique=True)

    # связи
    users: Mapped[List["UserNew"]] = relationship(
        secondary=new_user_roles, back_populates="roles"
    )
