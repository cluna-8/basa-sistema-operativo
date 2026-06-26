from sqlalchemy import BigInteger, String, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class HojaRuta(Base):
    __tablename__ = "hoja_ruta"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    fecha: Mapped[Date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDIENTE")
    transportista_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
