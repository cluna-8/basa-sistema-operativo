from sqlalchemy import BigInteger, String, Numeric, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Requerimiento(Base):
    __tablename__ = "requerimiento"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    requerimiento_tipo_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDIENTE")
    cliente_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    direccion_entrega_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    cantidad: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    fletes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    horas_archivista: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(String(8000), nullable=True)
    parent_requerimiento_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("dbo.requerimiento.id"), nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
