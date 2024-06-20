from typing import List

from litestar.contrib.sqlalchemy.base import UUIDAuditBase
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Country(UUIDAuditBase):
    __tablename__ = "countries"

    iso: Mapped[str] = mapped_column(String(3))
    name: Mapped[str] = mapped_column(String)

    streams: Mapped[List["Stream"]] = relationship(
        back_populates="country", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Country(id={self.id!r}, iso={self.iso!r}, name={self.name!r})"
