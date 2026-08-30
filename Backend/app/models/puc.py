from __future__ import annotations
from typing import TYPE_CHECKING
from schemas import Puc as PucSchema
from database import Base
from sqlalchemy import CheckConstraint, CHAR, Any
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

if TYPE_CHECKING:
    from models.comprobante import LineaContable


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

# Db operaciones

def get_cuentas(db: Session, activo: bool | None, skip: int = 0, limit: int = 100) -> list[Puc]:
    query = db.query(Puc)
    if activo is not None:
        query = query.filter(Puc.activo == activo)
    return query.order_by(Puc.codigo).offset(skip).limit(limit).all()

def get_cuenta(db: Session, codigo: str) -> Puc | None:
    return db.query(Puc).filter(Puc.codigo == codigo).first()

def create_cuenta(db: Session, cuenta: PucSchema) -> Puc:
    db_cuenta = Puc(
        codigo=cuenta.codigo,
        nombre=cuenta.nombre,
        naturaleza=cuenta.naturaleza,
        activo=cuenta.activo
    )
    db.add(db_cuenta)
    db.commit()
    db.refresh(db_cuenta)
    return db_cuenta

def update_cuenta(db: Session, codigo: str, cuenta: PucSchema) -> Puc | None:
    db_cuenta = db.query(Puc).filter(Puc.codigo == codigo).first()
    if db_cuenta is None:
        return None
    db_cuenta.nombre = cuenta.nombre
    db_cuenta.naturaleza = cuenta.naturaleza
    db_cuenta.activo = cuenta.activo
    db.commit()
    db.refresh(db_cuenta)
    return db_cuenta

def delete_cuenta(db: Session, codigo: str) -> bool:
    db_cuenta = db.query(Puc).filter(Puc.codigo == codigo).first()
    if db_cuenta is None:
        return False
    db_cuenta.activo = False
    db.commit()
    db.refresh(db_cuenta)
    return True