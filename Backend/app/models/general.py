from __future__ import annotations
from typing import TYPE_CHECKING
from app.database import Base
from sqlalchemy import Boolean, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal

if TYPE_CHECKING:
    from app.models.comprobante import Comprobante
    from app.models.periodo_contable import PeriodoContable

class Estado(Base):
    __tablename__: str = "estado"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(nullable=False)

    periodos: Mapped[list['PeriodoContable']] = relationship(back_populates='estado')
    comprobantes: Mapped[list['Comprobante']] = relationship(back_populates='estado')

class UvtValor(Base):
    __tablename__: str = "uvt_valor"

    anio: Mapped[int] = mapped_column(primary_key=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fuente: Mapped[str | None] = mapped_column(nullable=True)
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(nullable=True)

class UvtActualizacionLog(Base):
    __tablename__: str = "uvt_actualizacion_log"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    fecha: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    fuente: Mapped[str] = mapped_column(nullable=False)
    exitoso: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    anio: Mapped[int | None] = mapped_column(nullable=True)
    valor: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)

class GeneracionExogena(Base):
    __tablename__: str = "generacion_exogena"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    fecha_generacion: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    anio_gravable: Mapped[int] = mapped_column(nullable=False)
    umbral_uvt: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    valor_uvt: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    registros_incluidos: Mapped[int] = mapped_column(nullable=False, default=0)
    registros_excluidos: Mapped[int] = mapped_column(nullable=False, default=0)
    total_valor_bruto: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False, default=0)
    total_retencion: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False, default=0)
    ruta_archivo: Mapped[str] = mapped_column(Text, nullable=False)
    nombre_archivo: Mapped[str] = mapped_column(nullable=False)

    empresa_id: Mapped[int] = mapped_column(ForeignKey('empresa.id'), nullable=False)