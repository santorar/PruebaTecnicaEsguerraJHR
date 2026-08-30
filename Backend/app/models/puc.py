from __future__ import annotations
from typing import TYPE_CHECKING, Any
from app.database import Base
from sqlalchemy import CheckConstraint, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.comprobante import LineaContable


class Puc(Base):
    __tablename__: str = "puc"

    codigo: Mapped[str] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(nullable=False)
    naturaleza: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    activo: Mapped[bool] = mapped_column(default=True)

    __table_args__: tuple[Any, ...] = (
        CheckConstraint(
            "naturaleza IN ('D', 'C')", name='chk_naturaleza'
        ),
    )

    lineas: Mapped[list['LineaContable']] = relationship(back_populates='cuenta_rel')
