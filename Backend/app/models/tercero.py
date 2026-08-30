from __future__ import annotations
from typing import TYPE_CHECKING
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

if TYPE_CHECKING:
    from models.comprobante import LineaContable

class TipoDocumento(Base):
    __tablename__: str = "tipo_documento"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(nullable=False)

    terceros: Mapped[list['Tercero']] = relationship(back_populates='tipo_documento')


class Tercero(Base):
    __tablename__: str = "tercero"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(nullable=False)
    numero_documento: Mapped[str] = mapped_column(nullable=False)

    tipo_documento_id: Mapped[int] = mapped_column(ForeignKey('tipo_documento.id'), nullable=False)

    tipo_documento: Mapped['TipoDocumento'] = relationship(back_populates='terceros')
    lineas: Mapped[list['LineaContable']] = relationship(back_populates='tercero')