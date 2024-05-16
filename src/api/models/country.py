from sqlalchemy.orm import DeclaritiveBase, Mapped, String, mapped_column


class Country(DeclaritiveBase):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    iso: Mapped[str] = mapped_column(String(3))
    name: Mapped[str] = mapped_column(String)

    def __repr__(self) -> str:
        return f"Country(id={self.id!r}, iso={self.iso!r}, name={self.name!r})"
