from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base


class DanNew(Base):
    __tablename__ = 'dans'

    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(255), default=None)