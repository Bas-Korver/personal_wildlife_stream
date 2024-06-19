from typing import List, TYPE_CHECKING
from sqlalchemy import Double, String, ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from litestar.contrib.sqlalchemy.base import UUIDAuditBase


class StreamTag(UUIDAuditBase):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String, nullable=True)

    streams: Mapped[List["Stream"]] = relationship(
        back_populates="tag", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"StreamTag(id={self.id!r}, name={self.name!r}, model={self.model!r})"


class Stream(UUIDAuditBase):
    __tablename__ = "streams"

    name: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"))
    country_id: Mapped[str] = mapped_column(ForeignKey("countries.id"))
    location: Mapped[str] = mapped_column(String)
    latitude: Mapped[float] = mapped_column(Double)
    longitude: Mapped[float] = mapped_column(Double)

    tag: Mapped["StreamTag"] = relationship(back_populates="streams")
    country: Mapped["Country"] = relationship(back_populates="streams")
    animals: Mapped[List["Animal"]] = relationship(
        secondary="streams_animals",
        back_populates="streams",
    )

    def __repr__(self) -> str:
        return f"Stream(id={self.id!r}, name={self.name!r}, url={self.url!r}, tag={self.tag_id!r}, country_id={self.country_id!r}, location={self.location!r}, latitude={self.latitude!r}, longitude={self.longitude!r})"
