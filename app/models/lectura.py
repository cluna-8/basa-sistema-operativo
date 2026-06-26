from sqlalchemy import BigInteger, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Lectura(Base):
    __tablename__ = "lectura"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    remito: Mapped[str] = mapped_column(String(100), nullable=False)
    requerimiento_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("dbo.requerimiento.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # CLIENTE | PLANTA
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


class LecturaDetalle(Base):
    __tablename__ = "lectura_detalle"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lectura_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("dbo.lectura.id"), nullable=False)
    codigo_barra: Mapped[str] = mapped_column(String(100), nullable=False)
    resultado: Mapped[str] = mapped_column(String(20), nullable=False, default="ENCONTRADO")
