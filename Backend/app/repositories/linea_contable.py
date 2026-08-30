from sqlalchemy.orm import Session, joinedload
from app.models.comprobante import LineaContable


def get_lineas_comprobante(db: Session, comprobante_id: int) -> list[LineaContable]:
    return db.query(LineaContable).options(
        joinedload(LineaContable.cuenta_rel),
        joinedload(LineaContable.tercero)
    ).filter(LineaContable.comprobante_id == comprobante_id).all()


def get_linea(db: Session, linea_id: int) -> LineaContable | None:
    return db.query(LineaContable).options(
        joinedload(LineaContable.cuenta_rel),
        joinedload(LineaContable.tercero)
    ).filter(LineaContable.id == linea_id).first()


def get_linea_by_id_and_comprobante(db: Session, linea_id: int, comprobante_id: int) -> LineaContable | None:
    return db.query(LineaContable).options(
        joinedload(LineaContable.cuenta_rel),
        joinedload(LineaContable.tercero)
    ).filter(LineaContable.id == linea_id, LineaContable.comprobante_id == comprobante_id).first()


def create_linea(db: Session, descripcion: str | None, debito: float, credito: float, cuenta: str, tercero_id: int | None, comprobante_id: int) -> LineaContable:
    db_linea = LineaContable(
        descripcion=descripcion,
        debito=debito,
        credito=credito,
        cuenta=cuenta,
        tercero_id=tercero_id,
        comprobante_id=comprobante_id
    )
    db.add(db_linea)
    db.commit()
    db.refresh(db_linea)
    return db_linea


def update_linea(db: Session, db_linea: LineaContable, descripcion: str | None, debito: float, credito: float, cuenta: str, tercero_id: int | None) -> LineaContable:
    db_linea.descripcion = descripcion
    db_linea.debito = debito
    db_linea.credito = credito
    db_linea.cuenta = cuenta
    db_linea.tercero_id = tercero_id
    db.commit()
    db.refresh(db_linea)
    return db_linea


def delete_linea(db: Session, db_linea: LineaContable) -> bool:
    db.delete(db_linea)
    db.commit()
    return True
