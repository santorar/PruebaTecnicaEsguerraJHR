from __future__ import annotations
from typing import TYPE_CHECKING
from app.database import Base
from datetime import datetime
from sqlalchemy import Text, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

if TYPE_CHECKING:
    from app.models.empresa import Empresa
    from app.models.periodo_contable import PeriodoContable
    from app.models.usuario import Usuario
    from app.models.puc import Puc
    from app.models.tercero import Tercero
    from app.models.general import Estado

class Comprobante(Base):
    __tablename__: str = "comprobante"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    fecha_actualizacion: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())
    fecha_contabilizacion: Mapped[datetime | None] = mapped_column(nullable=True)

    empresa_id: Mapped[int] = mapped_column(ForeignKey('empresa.id'), nullable=False)
    periodo_contable_id: Mapped[int] = mapped_column(ForeignKey('periodo_contable.id'), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey('usuario.id'), nullable=False)
    estado_id: Mapped[int] = mapped_column(ForeignKey('estado.id'), nullable=False)
    comprobante_reversor_id: Mapped[int | None] = mapped_column(ForeignKey('comprobante.id'), nullable=True)
    comprobante_sustituto_id: Mapped[int | None] = mapped_column(ForeignKey('comprobante.id'), nullable=True)
    comprobante_original_id: Mapped[int | None] = mapped_column(ForeignKey('comprobante.id'), nullable=True)


    empresa: Mapped['Empresa'] = relationship(back_populates='comprobantes')
    periodo_contable: Mapped['PeriodoContable'] = relationship(back_populates='comprobantes')
    usuario: Mapped['Usuario'] = relationship(back_populates='comprobantes')
    estado: Mapped['Estado'] = relationship(back_populates='comprobantes')
    lineas: Mapped[list['LineaContable']] = relationship(back_populates='comprobante')
    comprobante_reversor: Mapped['Comprobante | None'] = relationship(foreign_keys=[comprobante_reversor_id])
    comprobante_sustituto: Mapped['Comprobante | None'] = relationship(foreign_keys=[comprobante_sustituto_id])
    comprobante_original: Mapped['Comprobante | None'] = relationship(foreign_keys=[comprobante_original_id])

class LineaContable(Base):
    __tablename__: str = "linea_contable"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    descripcion: Mapped[str | None] = mapped_column(nullable=True)
    debito: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    credito: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)

    cuenta: Mapped[str] = mapped_column(ForeignKey('puc.codigo'), nullable=False)
    tercero_id: Mapped[int | None] = mapped_column(ForeignKey('tercero.id'), nullable=True)
    comprobante_id: Mapped[int] = mapped_column(ForeignKey('comprobante.id'), nullable=False)

    cuenta_rel: Mapped['Puc'] = relationship(back_populates='lineas')
    tercero: Mapped['Tercero | None'] = relationship(back_populates='lineas')
    comprobante: Mapped['Comprobante'] = relationship(back_populates='lineas')