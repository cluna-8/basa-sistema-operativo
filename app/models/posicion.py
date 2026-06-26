from sqlalchemy import BigInteger, String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Posicion(Base):
    __tablename__ = "posicion"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="DISPONIBLE")
    estanteria: Mapped[int | None] = mapped_column(Numeric(18, 0), nullable=True)
    codigo_modulo: Mapped[str | None] = mapped_column(String(12), nullable=True)
    modulo_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
