from __future__ import annotations
from typing import TYPE_CHECKING
from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, text

if TYPE_CHECKING:
    from app.models.comprobante import Comprobante
    from app.models.empresa import Empresa


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(nullable=False, index=True)
    correo: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    clave_encriptada: Mapped[str] = mapped_column(nullable=False)
    activo: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)

    empresa_id: Mapped[int] = mapped_column(ForeignKey('empresa.id'))
    empresa: Mapped['Empresa'] = relationship(back_populates='usuarios')
    comprobantes: Mapped[list['Comprobante']] = relationship(back_populates='usuario')