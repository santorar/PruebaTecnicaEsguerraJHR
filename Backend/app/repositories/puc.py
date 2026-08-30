from sqlalchemy.orm import Session
from app.models.puc import Puc


def get_cuentas(db: Session, activo: bool | None, skip: int = 0, limit: int = 100) -> list[Puc]:
    query = db.query(Puc)
    if activo is not None:
        query = query.filter(Puc.activo == activo)
    return query.order_by(Puc.codigo).offset(skip).limit(limit).all()


def get_cuenta(db: Session, codigo: str) -> Puc | None:
    return db.query(Puc).filter(Puc.codigo == codigo).first()


def create_cuenta(db: Session, codigo: str, nombre: str, naturaleza: str, activo: bool) -> Puc:
    db_cuenta = Puc(
        codigo=codigo,
        nombre=nombre,
        naturaleza=naturaleza,
        activo=activo
    )
    db.add(db_cuenta)
    db.commit()
    db.refresh(db_cuenta)
    return db_cuenta


def update_cuenta(db: Session, db_cuenta: Puc, nombre: str, naturaleza: str, activo: bool) -> Puc:
    db_cuenta.nombre = nombre
    db_cuenta.naturaleza = naturaleza
    db_cuenta.activo = activo
    db.commit()
    db.refresh(db_cuenta)
    return db_cuenta


def delete_cuenta(db: Session, db_cuenta: Puc) -> Puc:
    db_cuenta.activo = False
    db.commit()
    db.refresh(db_cuenta)
    return db_cuenta
