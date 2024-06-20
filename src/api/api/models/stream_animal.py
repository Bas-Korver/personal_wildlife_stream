from typing import List
from uuid import UUID

from litestar.contrib.sqlalchemy.base import UUIDAuditBase
from sqlalchemy import Column, ForeignKey, Integer, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Integer


class StreamAnimal(UUIDAuditBase):
    __tablename__ = "stream_animal"

    stream_id: Mapped[UUID] = mapped_column(ForeignKey("streams.id"), primary_key=True)
    animal_id: Mapped[UUID] = mapped_column(ForeignKey("animals.id"), primary_key=True)
    count: Mapped[int] = mapped_column(Integer)

    stream: Mapped["Stream"] = relationship(back_populates="stream_animals")
    animal: Mapped["Animal"] = relationship(back_populates="stream_animals")

    __table_args__ = (
        UniqueConstraint("stream_id", "animal_id", name="stream_animal_uc"),
    )
