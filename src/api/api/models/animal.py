from typing import List

from litestar.contrib.sqlalchemy.base import UUIDAuditBase
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Animal(UUIDAuditBase):
    __tablename__ = "animals"

    common_name: Mapped[str] = mapped_column(String, unique=True)
    scientific_name: Mapped[str] = mapped_column(String)
    taxonomic_hierarchy: Mapped[dict] = mapped_column(JSONB)
    subspecies: Mapped[List[str]] = mapped_column(JSONB)

    stream_animals: Mapped[List["StreamAnimal"]] = relationship(back_populates="animal")

    def __repr__(self) -> str:
        return f"Animal(id={self.id!r}, common_name={self.name!r}, scientific_name={self.scientific_name!r})"
