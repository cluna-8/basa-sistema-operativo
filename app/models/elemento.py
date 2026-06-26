from sqlalchemy import BigInteger, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Elemento(Base):
    __tablename__ = "elemento"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="en guarda")
    posicion_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("dbo.posicion.id"), nullable=True, unique=True)
    elemento_tipo_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    cliente_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
