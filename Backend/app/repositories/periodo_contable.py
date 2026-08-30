from sqlalchemy.orm import Session, joinedload
from app.models.periodo_contable import PeriodoContable
from app.models.general import Estado
from app.models.comprobante import Comprobante
from app.schemas import PeriodoContable as PeriodoContableSchema

def get_periodos_contables(db: Session, skip: int = 0, limit: int = 100) -> list[PeriodoContable]:
    return db.query(PeriodoContable).options(
        joinedload(PeriodoContable.estado)
    ).offset(skip).limit(limit).all()

def get_periodo_contable(db: Session, id: int) -> PeriodoContable | None:
    return db.query(PeriodoContable).options(
        joinedload(PeriodoContable.estado)
    ).filter(PeriodoContable.id == id).first()

def get_periodo_contable_activo(db: Session, id: int) -> PeriodoContable | None:
    estado_activo = db.query(Estado).filter(Estado.nombre == "abierto").first()
    if estado_activo is None:
        raise Exception("Estado 'abierto' no encontrado en la base de datos")

    return db.query(PeriodoContable).filter(PeriodoContable.id == id, PeriodoContable.estado_id == estado_activo.id).first()

def get_periodo_contable_activo_for_update(db: Session, id: int) -> PeriodoContable | None:
    estado_activo = db.query(Estado).filter(Estado.nombre == "abierto").first()
    if estado_activo is None:
        raise Exception("Estado 'abierto' no encontrado en la base de datos")

    return db.query(PeriodoContable).filter(
        PeriodoContable.id == id, 
        PeriodoContable.estado_id == estado_activo.id
    ).with_for_update().first()

def get_estado_periodo(db: Session, periodo_id: int) -> Estado | None:
    periodo = db.query(PeriodoContable).filter(PeriodoContable.id == periodo_id).first()
    if periodo is None:
        return None
    return db.query(Estado).filter(Estado.id == periodo.estado_id).first()

def tiene_comprobantes(db: Session, periodo_id: int) -> bool:
    return db.query(Comprobante).filter(Comprobante.periodo_contable_id == periodo_id).count() > 0

def create_periodo_contable(db: Session, periodo: PeriodoContableSchema) -> PeriodoContable:
    estado_abierto = db.query(Estado).filter(Estado.nombre == "abierto").first()
    if estado_abierto is None:
        raise Exception("Estado 'abierto' no encontrado en la base de datos")

    db_periodo = PeriodoContable(
        nombre=periodo.nombre,
        fecha_inicio=periodo.fecha_inicio,
        fecha_fin=periodo.fecha_fin,
        estado_id=estado_abierto.id,
    )
    db.add(db_periodo)
    db.commit()
    db.refresh(db_periodo)
    return db_periodo

def update_periodo_contable(db: Session, periodo_id: int, periodo: PeriodoContableSchema) -> PeriodoContable | None:
    db_periodo = db.query(PeriodoContable).filter(PeriodoContable.id == periodo_id).first()
    if db_periodo is None:
        return None
    db_periodo.nombre = periodo.nombre
    db_periodo.fecha_inicio = periodo.fecha_inicio
    db_periodo.fecha_fin = periodo.fecha_fin
    db.commit()
    db.refresh(db_periodo)
    return db_periodo

def update_periodo_contable_estado(db: Session, periodo_id: int, estado_id: int) -> PeriodoContable | None:
    db_periodo = db.query(PeriodoContable).filter(PeriodoContable.id == periodo_id).first()
    if db_periodo is None:
        return None
    db_periodo.estado_id = estado_id
    db.commit()
    db.refresh(db_periodo)
    return db_periodo

def delete_periodo_contable(db: Session, periodo_id: int) -> bool:
    db_periodo = db.query(PeriodoContable).filter(PeriodoContable.id == periodo_id).first()
    if db_periodo is None:
        return False
    db.delete(db_periodo)
    db.commit()
    return True
