from typing import List

from litestar.contrib.sqlalchemy.base import UUIDAuditBase
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Animal(UUIDAuditBase):
    __tablename__ = "animals"

    name: Mapped[str] = mapped_column(String, unique=True)

    stream_animals: Mapped[List["StreamAnimal"]] = relationship(back_populates="animal")

    def __repr__(self) -> str:
        return f"Animal(id={self.id!r}, name={self.name!r})"
