from sqlalchemy.orm import (
    DeclaritiveBase,
    Double,
    List,
    Mapped,
    String,
    mapped_column,
    relationship,
)


class StreamTag(DeclaritiveBase):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)

    def __repr__(self) -> str:
        return f"StreamTag(id={self.id!r}, name={self.name!r})"


class Stream(DeclaritiveBase):
    __tablename__ = "streams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    tag: Mapped["StreamTag"] = relationship(back_populates="tags")
    country: Mapped["Country"] = relationship(back_populates="countries")
    location: Mapped[str] = mapped_column(String)
    latitude: Mapped[float] = mapped_column(Double)
    longitude: Mapped[float] = mapped_column(Double)

    def __repr__(self) -> str:
        return f"Stream(id={self.id!r}, name={self.name!r}, url={self.url!r}, tag={self.tag.name!r}, country={self.country.name!r}, location={self.location!r}, latitude={self.latitude!r}, longitude={self.longitude!r})"
