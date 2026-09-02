from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.schemas import Comprobante as ComprobanteSchema, LibroMayorRequest
from app.models.comprobante import Comprobante, LineaContable
from app.models.general import Estado

def get_comprobantes(db: Session, estado_id: int | None, skip: int = 0, limit: int = 100) -> list[Comprobante]:
    query = db.query(Comprobante)
    if estado_id is not None:
        query = query.filter(Comprobante.estado_id == estado_id)
    return query.options(
        joinedload(Comprobante.lineas).joinedload(LineaContable.cuenta_rel),
        joinedload(Comprobante.estado),
        joinedload(Comprobante.comprobante_reversor),
        joinedload(Comprobante.comprobante_sustituto),
        joinedload(Comprobante.comprobante_original),
    ).offset(skip).limit(limit).all()

def get_comprobante(db: Session, comprobante_id: int) -> Comprobante | None:
    return db.query(Comprobante).options(
        joinedload(Comprobante.lineas).joinedload(LineaContable.cuenta_rel),
        joinedload(Comprobante.estado),
        joinedload(Comprobante.comprobante_reversor),
        joinedload(Comprobante.comprobante_sustituto),
        joinedload(Comprobante.comprobante_original),
    ).filter(Comprobante.id == comprobante_id).first()

def get_comprobante_for_update(db: Session, comprobante_id: int) -> Comprobante | None:
    db.query(Comprobante).filter(Comprobante.id == comprobante_id).with_for_update().first()
    return db.query(Comprobante).options(
        joinedload(Comprobante.lineas).joinedload(LineaContable.cuenta_rel),
        joinedload(Comprobante.estado),
        joinedload(Comprobante.comprobante_reversor),
        joinedload(Comprobante.comprobante_sustituto),
        joinedload(Comprobante.comprobante_original),
    ).filter(Comprobante.id == comprobante_id).first()

def get_comprobante_estado(db: Session, comprobante_id: int) -> Estado | None:
    comprobante = db.query(Comprobante).filter(Comprobante.id == comprobante_id).first()
    if comprobante is None:
        return None
    return db.query(Estado).filter(Estado.id == comprobante.estado_id).first()


def create_comprobante(db: Session, comprobante: ComprobanteSchema, esNuevo: bool = True) -> Comprobante:
    estado_borrador = db.query(Estado).filter(Estado.nombre == "borrador").first()
    if estado_borrador is None:
        raise Exception("Estado 'borrador' no encontrado en la base de datos")
    # Si no viene un estado explicito (p. ej. el sustituto de una reversion),
    # se resuelve 'borrador' por nombre en lugar de depender de un id fijo.
    estado_id = estado_borrador.id if esNuevo or comprobante.estado_id is None else comprobante.estado_id

    db_comprobante = Comprobante(
        descripcion=comprobante.descripcion,
        empresa_id=comprobante.empresa_id,
        periodo_contable_id=comprobante.periodo_contable_id,
        usuario_id=comprobante.usuario_id,
        estado_id=estado_id,
        comprobante_original_id=comprobante.comprobante_original_id
    )
    
    if not esNuevo and estado_id is not None:
        estado = db.query(Estado).filter(Estado.id == estado_id).first()
        if estado and estado.nombre == "contabilizado":
            db_comprobante.fecha_contabilizacion = datetime.now()
    
    for linea in comprobante.lineas:
        db_linea = LineaContable(
            descripcion=linea.descripcion,
            debito=linea.debito,
            credito=linea.credito,
            cuenta=linea.cuenta,
            tercero_id=linea.tercero_id
        )
        db_comprobante.lineas.append(db_linea)
    db.add(db_comprobante)
    db.commit()
    db.refresh(db_comprobante)
    return db_comprobante

def update_comprobante(db: Session, comprobante_id: int, comprobante: ComprobanteSchema) -> Comprobante | None:
    db_comprobante = db.query(Comprobante).filter(Comprobante.id == comprobante_id).first()
    if db_comprobante is None:
        return None
    db_comprobante.descripcion = comprobante.descripcion
    db_comprobante.empresa_id = comprobante.empresa_id
    db_comprobante.periodo_contable_id = comprobante.periodo_contable_id
    db_comprobante.usuario_id = comprobante.usuario_id
    db_comprobante.fecha_actualizacion = datetime.now()
    # Si se indica que se deben actualizar las lineas, lo hacemos
    db.query(LineaContable).filter(LineaContable.comprobante_id == comprobante_id).delete()
    for linea in comprobante.lineas:
        db_linea = LineaContable(
            descripcion=linea.descripcion,
            debito=linea.debito,
            credito=linea.credito,
            cuenta=linea.cuenta,
            tercero_id=linea.tercero_id
        )
        db_comprobante.lineas.append(db_linea)

    db.commit()
    db.refresh(db_comprobante)
    return db_comprobante

def update_comprobante_estado(db: Session, comprobante_id: int, estado_id: int) -> Comprobante | None:
    db_comprobante = db.query(Comprobante).filter(Comprobante.id == comprobante_id).first()
    if db_comprobante is None:
        return None
    estado = db.query(Estado).filter(Estado.id == estado_id).first()
    if estado is None:
        raise Exception("Estado no encontrado")
    if estado.nombre == "contabilizado":
        db_comprobante.fecha_contabilizacion = datetime.now()
    db_comprobante.fecha_actualizacion = datetime.now()
    db_comprobante.estado_id = estado_id
    db.commit()
    db.refresh(db_comprobante)
    return db_comprobante

def update_comprobante_anulacion(db: Session, comprobante: Comprobante, comprobante_reversor_id: int, comprobante_sustituto_id: int):
    estado_anulado = db.query(Estado).filter(Estado.nombre == "anulado").first()
    if estado_anulado is None:
        raise Exception("Estado no encontrado")
    comprobante.estado_id = estado_anulado.id
    comprobante.comprobante_reversor_id = comprobante_reversor_id
    comprobante.comprobante_sustituto_id = comprobante_sustituto_id
    comprobante.fecha_actualizacion = datetime.now()
    db.commit()
    db.refresh(comprobante)
    return comprobante


def delete_comprobante(db: Session, comprobante_id: int) -> bool:
    db_comprobante = db.query(Comprobante).filter(Comprobante.id == comprobante_id).first()
    if db_comprobante is None:
        return False
    db.query(LineaContable).filter(LineaContable.comprobante_id == comprobante_id).delete()
    db.delete(db_comprobante)
    db.commit()
    return True