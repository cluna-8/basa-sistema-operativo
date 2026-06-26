from sqlalchemy import BigInteger, String, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Movimiento(Base):
    __tablename__ = "movimiento"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    elemento_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("dbo.elemento.id"), nullable=True)
    requerimiento_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("dbo.requerimiento.id"), nullable=True)
    tipo_movimiento: Mapped[str] = mapped_column(String(100), nullable=False)
    estado_anterior: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estado_nuevo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    operario_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
