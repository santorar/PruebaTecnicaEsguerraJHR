from __future__ import annotations
from typing import TYPE_CHECKING
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from datetime import date

if TYPE_CHECKING:
    from models.general import Estado
    from models.comprobante import Comprobante

class PeriodoContable(Base):
    __tablename__: str = "periodo_contable"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(nullable=False)
    fecha_fin: Mapped[date] = mapped_column(nullable=False)
    estado_id: Mapped[int] = mapped_column(ForeignKey('estado.id'), nullable=False, default=1)

    estado: Mapped['Estado'] = relationship(back_populates='periodos')
    comprobantes: Mapped[list['Comprobante']] = relationship(back_populates='periodo_contable')