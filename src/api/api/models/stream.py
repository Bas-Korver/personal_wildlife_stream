from typing import List
from sqlalchemy import Double, String, ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from db.postgres import Base


class StreamTag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String, nullable=True)

    streams: Mapped[List["Stream"]] = relationship(
        back_populates="tag", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"StreamTag(id={self.id!r}, name={self.name!r})"


class Stream(Base):
    __tablename__ = "streams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"))
    country_iso: Mapped[str] = mapped_column(ForeignKey("countries.iso"))
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
        return f"Stream(id={self.id!r}, name={self.name!r}, url={self.url!r}, tag={self.tag_id!r}, country_iso={self.country_iso!r}, location={self.location!r}, latitude={self.latitude!r}, longitude={self.longitude!r})"
