from sqlalchemy.orm import (
    DeclaritiveBase,
    List,
    Mapped,
    String,
    mapped_column,
    relationship,
)


class Country(DeclaritiveBase):
    __tablename__ = "countries"

    iso: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String)

    streams: Mapped[List["Stream"]] = relationship(
        back_populates="country", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Country(iso={self.iso!r}, name={self.name!r})"
