from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.schemas import LibroMayorRequest
from app.models.comprobante import Comprobante, LineaContable
from app.models.general import Estado, GeneracionExogena
from app.models.tercero import Tercero, TipoDocumento
from sqlalchemy import and_, or_, func

def get_comprobante_libro_mayor(db: Session, request: LibroMayorRequest):
    estado_contabilizado = db.query(Estado).filter(Estado.nombre == "contabilizado").first()
    if estado_contabilizado is None:
        return []
    estado_anulado = db.query(Estado).filter(Estado.nombre == "anulado").first()
    if estado_anulado is None:
        return []
    
    fecha_inicial_dt = datetime.combine(request.fecha_inicial, datetime.min.time())
    fecha_final_dt = datetime.combine(request.fecha_final, datetime.max.time())

    lineas = db.query(LineaContable).options(
        joinedload(LineaContable.tercero),
        joinedload(LineaContable.comprobante)
    ).join(Comprobante).filter(
        and_(
            LineaContable.cuenta == request.cuenta,
            or_(
                Comprobante.estado_id == estado_contabilizado.id,
                Comprobante.estado_id == estado_anulado.id,
            ),
            Comprobante.fecha_contabilizacion >= fecha_inicial_dt,
            Comprobante.fecha_contabilizacion <= fecha_final_dt
        )
    ).order_by(Comprobante.fecha_contabilizacion, LineaContable.id).all()
    return lineas

def get_movimientos_exogena(db: Session, fecha_inicial: datetime, fecha_final: datetime):
    estado_contabilizado = db.query(Estado).filter(Estado.nombre == "contabilizado").first()
    if estado_contabilizado is None:
        return []
    estado_anulado = db.query(Estado).filter(Estado.nombre == "anulado").first()
    if estado_anulado is None:
        return []

    return db.query(
        Tercero.id.label('tercero_id'),
        Tercero.nombre.label('tercero_nombre'),
        Tercero.numero_documento.label('tercero_documento'),
        TipoDocumento.nombre.label('tipo_documento'),
        LineaContable.cuenta.label('cuenta'),
        (func.sum(LineaContable.debito) - func.sum(LineaContable.credito)).label('neto'),
    ).join(
        Comprobante, LineaContable.comprobante_id == Comprobante.id
    ).join(
        Tercero, LineaContable.tercero_id == Tercero.id
    ).join(
        TipoDocumento, Tercero.tipo_documento_id == TipoDocumento.id
    ).filter(
        and_(
            or_(
                Comprobante.estado_id == estado_contabilizado.id,
                Comprobante.estado_id == estado_anulado.id,
            ),
            LineaContable.tercero_id.isnot(None),
            Comprobante.fecha_contabilizacion >= fecha_inicial,
            Comprobante.fecha_contabilizacion <= fecha_final,
        )
    ).group_by(
        Tercero.id, Tercero.nombre, Tercero.numero_documento, TipoDocumento.nombre, LineaContable.cuenta
    ).order_by(
        Tercero.id, LineaContable.cuenta
    ).all()


def create_generacion_exogena(db: Session, generacion: GeneracionExogena) -> GeneracionExogena:
    db.add(generacion)
    db.flush()
    return generacion

def get_generaciones_exogena(db: Session, skip: int = 0, limit: int = 100) -> list[GeneracionExogena]:
    return db.query(GeneracionExogena).order_by(GeneracionExogena.id.desc()).offset(skip).limit(limit).all()

def get_generacion_exogena(db: Session, generacion_id: int) -> GeneracionExogena | None:
    return db.query(GeneracionExogena).filter(GeneracionExogena.id == generacion_id).first()