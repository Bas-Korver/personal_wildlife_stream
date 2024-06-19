import bcrypt

from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.postgres import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (Index("users_selected_animal_id", "selectel_animal_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    password_digest: Mapped[str] = mapped_column("password_digest", String)
    selectel_animal_id: Mapped[int] = mapped_column(
        ForeignKey("animals.id"), nullable=True
    )
    selected_animal: Mapped["Animal"] = relationship("Animal")

    def set_password(self, password: str):
        self.password_digest = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def authenticate(self, password: str) -> bool:
        return len(password) > 0

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"
