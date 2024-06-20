from typing import TYPE_CHECKING, List

from litestar.contrib.sqlalchemy.base import UUIDAuditBase
from sqlalchemy import Double, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


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
    url: Mapped[str] = mapped_column(String, unique=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"))
    country_id: Mapped[str] = mapped_column(ForeignKey("countries.id"))
    location: Mapped[str] = mapped_column(String)
    latitude: Mapped[float] = mapped_column(Double)
    longitude: Mapped[float] = mapped_column(Double)

    tag: Mapped["StreamTag"] = relationship(back_populates="streams")
    country: Mapped["Country"] = relationship(back_populates="streams")
    stream_animals: Mapped[List["StreamAnimal"]] = relationship(back_populates="stream")

    def __repr__(self) -> str:
        return f"Stream(id={self.id!r}, name={self.name!r}, url={self.url!r}, tag={self.tag_id!r}, country_id={self.country_id!r}, location={self.location!r}, latitude={self.latitude!r}, longitude={self.longitude!r})"
