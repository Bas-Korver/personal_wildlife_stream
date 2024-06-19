from typing import List
from sqlalchemy import String
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from models.base import Base


class Animal(Base):
    __tablename__ = "animals"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)

    streams: Mapped[List["Stream"]] = relationship(
        secondary="streams_animals",
        back_populates="animals",
    )

    def __repr__(self) -> str:
        return f"Animal(id={self.id!r}, name={self.name!r})"
