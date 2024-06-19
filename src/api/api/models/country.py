from typing import List
from sqlalchemy import String
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from models.base import Base
from models.stream import Stream


class Country(Base):
    __tablename__ = "countries"

    iso: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String)

    streams: Mapped[List["Stream"]] = relationship(
        back_populates="country", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Country(iso={self.iso!r}, name={self.name!r})"
