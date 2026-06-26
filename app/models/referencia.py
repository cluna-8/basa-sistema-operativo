from sqlalchemy import BigInteger, String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Referencia(Base):
    __tablename__ = "referencia"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    elemento_contenedor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("dbo.elemento.id"), nullable=False)
    texto1: Mapped[str | None] = mapped_column(String(500), nullable=True)
    texto2: Mapped[str | None] = mapped_column(String(500), nullable=True)
    numero1: Mapped[float | None] = mapped_column(Numeric, nullable=True)
